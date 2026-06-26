const API_URL = 'http://127.0.0.1:8000';

// Navigation Logic
const navBtns = document.querySelectorAll('.nav-btn');
const formSections = document.querySelectorAll('.disease-form-section');

navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all buttons and sections
        navBtns.forEach(b => b.classList.remove('active'));
        formSections.forEach(s => s.classList.remove('active'));
        
        // Add active class to clicked button and corresponding section
        btn.classList.add('active');
        const targetId = btn.getAttribute('data-target');
        document.getElementById(targetId).classList.add('active');
    });
});

// Generic form handler
async function handleFormSubmit(e, endpoint, dataMapper, resultContainerId) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerText;
    submitBtn.innerHTML = '<div class="loader"></div>';
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
            <div class="result-title">Prediction Result</div>
            <div class="result-value ${statusClass}">${data.prediction}</div>
            <div class="result-prob">Confidence: ${probPct}%</div>
        `;
        resultCard.classList.remove('hidden');

    } catch (error) {
        resultCard.innerHTML = `
            <div class="result-title">Error</div>
            <div class="result-value" style="color: var(--danger); font-size: 1.5rem;">${error.message}</div>
            <div class="result-prob">Make sure backend is running and models are trained.</div>
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
