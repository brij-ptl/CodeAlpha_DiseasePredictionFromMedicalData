const API_URL = 'http://127.0.0.1:8080';

// Initialize VanillaTilt for 3D cards
VanillaTilt.init(document.querySelectorAll(".tilt-card"), {
    max: 15,
    speed: 400,
    glare: true,
    "max-glare": 0.2,
});

// UI Logic
const cards = document.querySelectorAll('.tilt-card');
const formsSection = document.getElementById('forms-section');
const closeBtns = document.querySelectorAll('.close-btn');
const formContainers = document.querySelectorAll('.disease-form-section');

// Open Form Overlay when a card is clicked
cards.forEach(card => {
    card.addEventListener('click', () => {
        const targetId = card.getAttribute('data-target');
        
        // Hide all forms first
        formContainers.forEach(form => form.classList.remove('active'));
        
        // Show overlay and specific form
        formsSection.classList.add('active');
        document.getElementById(targetId).classList.add('active');
    });
});

// Close Form Overlay
const closeOverlay = () => {
    formsSection.classList.remove('active');
    setTimeout(() => {
        formContainers.forEach(form => {
            form.classList.remove('active');
            // Hide result cards too on close
            const resultCard = form.querySelector('.result-card');
            if(resultCard) resultCard.classList.add('hidden');
        });
    }, 400); // Wait for transition
};

closeBtns.forEach(btn => {
    btn.addEventListener('click', closeOverlay);
});

// Generic form handler for Predictions
async function handleFormSubmit(e, endpoint, dataMapper, resultContainerId) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerText;
    submitBtn.innerHTML = '<div class="loader" style="width:20px;height:20px;border:3px solid #000;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;"></div>';
    submitBtn.disabled = true;

    const resultCard = document.getElementById(resultContainerId);
    resultCard.classList.add('hidden');

    try {
        const payload = dataMapper(e.target);
        
        const response = await fetch(`${API_URL}/predict/${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error('API error or model not trained');
        }

        const data = await response.json();
        
        // Display result
        const isPositive = data.prediction === 'Malignant' || data.prediction === 'Positive' || data.prediction === 'Presence';
        const statusClass = isPositive ? 'status-positive' : 'status-negative';
        const probPct = (data.probability * 100).toFixed(1);
        
        resultCard.innerHTML = `
            <div style="font-size: 1rem; color: var(--text-secondary); margin-bottom: 0.5rem; letter-spacing: 1px; text-transform: uppercase;">AI Prediction Analysis</div>
            <div class="result-value ${statusClass}">${data.prediction}</div>
            <div style="font-size: 1.1rem; margin-top: 1rem; color: var(--accent-1);">Confidence Level: <strong>${probPct}%</strong></div>
        `;
        resultCard.classList.remove('hidden');

    } catch (error) {
        resultCard.innerHTML = `
            <div style="font-size: 1rem; color: var(--text-secondary); margin-bottom: 0.5rem;">Error Detected</div>
            <div class="result-value" style="color: var(--danger); font-size: 1.5rem;">Connection Failed</div>
            <div style="font-size: 0.9rem; margin-top: 1rem;">Make sure backend is running on port 8080.</div>
        `;
        resultCard.classList.remove('hidden');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// Attach event listeners to forms
document.getElementById('form-breast-cancer').addEventListener('submit', (e) => {
    handleFormSubmit(e, 'breast-cancer', (form) => ({
        mean_radius: parseFloat(document.getElementById('bc-radius').value),
        mean_texture: parseFloat(document.getElementById('bc-texture').value),
        mean_perimeter: parseFloat(document.getElementById('bc-perimeter').value),
        mean_area: parseFloat(document.getElementById('bc-area').value),
        mean_smoothness: parseFloat(document.getElementById('bc-smoothness').value)
    }), 'result-breast-cancer');
});

document.getElementById('form-diabetes').addEventListener('submit', (e) => {
    handleFormSubmit(e, 'diabetes', (form) => ({
        pregnancies: parseFloat(document.getElementById('diab-pregnancies').value),
        glucose: parseFloat(document.getElementById('diab-glucose').value),
        blood_pressure: parseFloat(document.getElementById('diab-bp').value),
        bmi: parseFloat(document.getElementById('diab-bmi').value),
        age: parseFloat(document.getElementById('diab-age').value)
    }), 'result-diabetes');
});

document.getElementById('form-heart-disease').addEventListener('submit', (e) => {
    handleFormSubmit(e, 'heart-disease', (form) => ({
        age: parseFloat(document.getElementById('hd-age').value),
        sex: parseFloat(document.getElementById('hd-sex').value),
        cp: parseFloat(document.getElementById('hd-cp').value),
        trestbps: parseFloat(document.getElementById('hd-trestbps').value),
        chol: parseFloat(document.getElementById('hd-chol').value)
    }), 'result-heart-disease');
});
