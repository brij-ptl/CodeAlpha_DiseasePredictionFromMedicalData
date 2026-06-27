/* ═══════════════════════════════════════════════════════════════════════════
   MediAI — app.js  v2.0
   New backend port: 5055  |  API prefix: /api/v1
   Handles: Modal, FAQ, Navbar, Counters, Forms, Rich Medical Report Renderer
═══════════════════════════════════════════════════════════════════════════ */

const API_URL = 'http://127.0.0.1:5055';
const API_PREFIX = '/api/v1';

/* ─────────────────────────── SMOOTH SCROLL ──────────────────────────────── */
function smoothScroll(id) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
window.smoothScroll = smoothScroll;

/* ─────────────────────────── NAVBAR ON SCROLL ───────────────────────────── */
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
}, { passive: true });

/* ─────────────────────────── MOBILE NAV TOGGLE ─────────────────────────── */
const navToggle = document.getElementById('navToggle');
navToggle.addEventListener('click', () => {
    const expanded = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!expanded));
    navbar.classList.toggle('mobile-open');
});

/* ────────────────────── INTERSECTION OBSERVER — FADE IN ─────────────────── */
const fadeEls = document.querySelectorAll('.fade-in-up');
const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const delay = entry.target.dataset.delay || 0;
            setTimeout(() => entry.target.classList.add('visible'), Number(delay));
            fadeObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.12 });
fadeEls.forEach(el => fadeObserver.observe(el));

/* ──────────────────────────── ANIMATED COUNTERS ─────────────────────────── */
const statValues = document.querySelectorAll('.stat-value[data-count]');
const countObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounter(entry.target);
            countObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });
statValues.forEach(el => countObserver.observe(el));

function animateCounter(el) {
    const target = parseInt(el.dataset.count, 10);
    const duration = 1600;
    const steps = 60;
    const increment = target / steps;
    let current = 0, frame = 0;
    const timer = setInterval(() => {
        frame++;
        current = Math.min(Math.round(increment * frame), target);
        el.textContent = current;
        if (current >= target) clearInterval(timer);
    }, duration / steps);
}

/* ──────────────────────────────── FAQ ───────────────────────────────────── */
const faqItems = document.querySelectorAll('.faq-item');
faqItems.forEach(item => {
    const question = item.querySelector('.faq-question');
    const answer   = item.querySelector('.faq-answer');
    question.addEventListener('click', () => {
        const isOpen = item.classList.contains('open');
        faqItems.forEach(i => {
            i.classList.remove('open');
            i.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
            i.querySelector('.faq-answer').hidden = true;
        });
        if (!isOpen) {
            item.classList.add('open');
            question.setAttribute('aria-expanded', 'true');
            answer.hidden = false;
        }
    });
});

/* ────────────────────────────── MODAL SYSTEM ────────────────────────────── */
const modalOverlay    = document.getElementById('forms-section');
const modalBackdrop   = document.getElementById('modalBackdrop');
const formContainers  = document.querySelectorAll('.disease-form-section');
const closeBtns       = document.querySelectorAll('.close-btn');
const assessmentCards = document.querySelectorAll('.assessment-card');

function openModal(targetId) {
    formContainers.forEach(f => { f.hidden = true; f.classList.remove('active'); });
    const panel = document.getElementById(targetId);
    if (!panel) return;
    panel.hidden = false;
    panel.classList.add('active');
    modalOverlay.classList.add('active');
    modalOverlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
        const firstInput = panel.querySelector('input, select');
        if (firstInput) firstInput.focus();
    }, 350);
}

function closeModal() {
    modalOverlay.classList.remove('active');
    modalOverlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    setTimeout(() => {
        formContainers.forEach(f => {
            f.hidden = true;
            f.classList.remove('active');
            const result = f.querySelector('.result-card');
            if (result) result.classList.add('hidden');
        });
    }, 350);
}

assessmentCards.forEach(card => {
    card.addEventListener('click', () => openModal(card.dataset.target));
    card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openModal(card.dataset.target); }
    });
});
closeBtns.forEach(btn => btn.addEventListener('click', closeModal));
modalBackdrop.addEventListener('click', closeModal);
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalOverlay.classList.contains('active')) closeModal();
});

/* ═══════════════════════════════════════════════════════════════════════════
   MEDICAL REPORT RENDERER
   Transforms the structured MedicalReport JSON into a rich HTML dashboard
═══════════════════════════════════════════════════════════════════════════ */

/**
 * Returns the colour scheme, icon, and label for a given risk level.
 */
function getRiskMeta(riskLevel) {
    const map = {
        'High':     { color: '#ff4d4d', bg: 'rgba(255,77,77,0.12)',  icon: '🔴', label: 'High Risk' },
        'Moderate': { color: '#ffb347', bg: 'rgba(255,179,71,0.12)', icon: '🟡', label: 'Moderate Risk' },
        'Low':      { color: '#4ade80', bg: 'rgba(74,222,128,0.12)', icon: '🟢', label: 'Low Risk' },
    };
    return map[riskLevel] || map['Low'];
}

/**
 * Returns badge HTML for a factor status.
 */
function getStatusBadge(status) {
    const map = {
        'Normal':     { color: '#4ade80', bg: 'rgba(74,222,128,0.15)'  },
        'Borderline': { color: '#ffb347', bg: 'rgba(255,179,71,0.15)'  },
        'Abnormal':   { color: '#ff4d4d', bg: 'rgba(255,77,77,0.15)'   },
    };
    const s = map[status] || map['Normal'];
    return `<span style="
        display:inline-block;
        padding:2px 10px;
        border-radius:20px;
        font-size:0.7rem;
        font-weight:700;
        letter-spacing:0.8px;
        color:${s.color};
        background:${s.bg};
        text-transform:uppercase;
    ">${status}</span>`;
}

/**
 * Renders a section card with a header icon and title.
 */
function reportSection(icon, title, content) {
    return `
    <div class="report-section-card">
        <div class="report-section-header">
            <span class="report-section-icon">${icon}</span>
            <h3 class="report-section-title">${title}</h3>
        </div>
        <div class="report-section-body">${content}</div>
    </div>`;
}

/**
 * Renders a list of strings as styled bullet points.
 */
function renderList(items, icon = '•') {
    if (!items || !items.length) return '<p style="color:var(--text-muted);font-style:italic;">No items available.</p>';
    return `<ul class="report-list">${items.map(i => `<li><span class="list-icon">${icon}</span><span>${i}</span></li>`).join('')}</ul>`;
}

/**
 * Renders the contributing factors table.
 */
function renderFactors(factors) {
    if (!factors || !factors.length) return '';
    return `
    <div class="factors-grid">
        ${factors.map(f => `
        <div class="factor-card">
            <div class="factor-header">
                <span class="factor-name">${f.name}</span>
                ${getStatusBadge(f.status)}
            </div>
            <div class="factor-value">${f.value}</div>
            <div class="factor-range">Normal: ${f.normal_range}</div>
            <p class="factor-interpretation">${f.interpretation}</p>
        </div>`).join('')}
    </div>`;
}

/**
 * Renders the lifestyle recommendations as grouped tabs.
 */
function renderLifestyle(lr) {
    const categories = [
        { key: 'diet',             icon: '🥗', label: 'Diet'            },
        { key: 'physical_activity',icon: '🏃', label: 'Exercise'        },
        { key: 'sleep',            icon: '😴', label: 'Sleep'           },
        { key: 'weight_management',icon: '⚖️', label: 'Weight'          },
        { key: 'hydration',        icon: '💧', label: 'Hydration'       },
        { key: 'stress_management',icon: '🧘', label: 'Stress'          },
        { key: 'smoking',          icon: '🚭', label: 'Smoking'         },
        { key: 'alcohol',          icon: '🍷', label: 'Alcohol'         },
    ];

    return `<div class="lifestyle-grid">
        ${categories.filter(c => lr[c.key] && lr[c.key].length).map(c => `
        <div class="lifestyle-category">
            <div class="lifestyle-category-header">
                <span>${c.icon}</span>
                <strong>${c.label}</strong>
            </div>
            ${renderList(lr[c.key], '→')}
        </div>`).join('')}
    </div>`;
}

/**
 * Main report rendering function.
 * Accepts the MedicalReport JSON object and renders the full dashboard.
 */
function renderMedicalReport(data, containerEl) {
    const risk = getRiskMeta(data.risk_level);
    const confPct = (data.confidence_score * 100).toFixed(1);
    const generatedAt = new Date(data.generated_at).toLocaleString();

    const html = `
    <div class="medical-report">

        <!-- ── REPORT HEADER ── -->
        <div class="report-header">
            <div class="report-header-left">
                <div class="report-specialist">${data.specialist_role}</div>
                <div class="report-disease-name">${data.disease_name} Risk Assessment</div>
                <div class="report-meta">Generated: ${generatedAt} &nbsp;|&nbsp; Model v${data.model_version}</div>
            </div>
            <div class="report-header-right">
                <div class="risk-badge-large" style="color:${risk.color};background:${risk.bg};border:1px solid ${risk.color}40;">
                    <span class="risk-icon">${risk.icon}</span>
                    <span class="risk-label">${risk.label}</span>
                </div>
            </div>
        </div>

        <!-- ── SECTION 1: PREDICTION SUMMARY ── -->
        <div class="report-summary-grid">
            <div class="summary-card primary">
                <div class="summary-label">Clinical Finding</div>
                <div class="summary-value" style="color:${risk.color}">${data.prediction_label}</div>
                <div class="summary-sub">AI Classification Result</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Confidence Score</div>
                <div class="summary-value">${confPct}%</div>
                <div class="confidence-bar-wrap">
                    <div class="confidence-bar" style="width:${confPct}%;background:${risk.color}"></div>
                </div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Risk Level</div>
                <div class="summary-value" style="color:${risk.color}">${data.risk_level}</div>
                <div class="summary-sub">${risk.icon} ${risk.label}</div>
            </div>
        </div>

        <div class="report-summary-text">${data.prediction_summary}</div>

        <!-- ── SECTION 2: EXPLANATION ── -->
        ${reportSection('🧠', 'Why the AI Reached This Conclusion', `<p class="report-para">${data.explanation}</p>`)}

        <!-- ── SECTION 3: CLINICAL INTERPRETATION ── -->
        ${reportSection('🩺', 'Clinical Interpretation', `
            <p class="report-para">${data.clinical_interpretation}</p>
            ${data.contributing_factors && data.contributing_factors.length
                ? `<h4 class="subsection-title">Key Medical Indicators</h4>${renderFactors(data.contributing_factors)}`
                : ''}
        `)}

        <!-- ── SECTION 4: LIFESTYLE RECOMMENDATIONS ── -->
        ${reportSection('🌿', 'Personalised Lifestyle Recommendations',
            data.lifestyle_recommendations ? renderLifestyle(data.lifestyle_recommendations) : ''
        )}

        <!-- ── SECTIONS 5 & 6: DO'S AND DON'TS ── -->
        <div class="dos-donts-grid">
            ${reportSection('✅', "Do's — Recommended Actions", renderList(data.dos, '✓'))}
            ${reportSection('❌', "Don'ts — What to Avoid", renderList(data.donts, '✗'))}
        </div>

        <!-- ── SECTION 7: WHEN TO SEE A DOCTOR ── -->
        ${reportSection('🏥', 'When to Consult a Doctor', `<p class="report-para urgent-note">${data.when_to_see_doctor}</p>`)}

        <!-- ── SECTION 8: PREVENTIVE CARE ── -->
        ${reportSection('🛡️', 'Preventive Care & Long-Term Monitoring', renderList(data.preventive_care, '📋'))}

        <!-- ── SECTION 9: IN SIMPLE WORDS ── -->
        ${reportSection('💬', 'In Simple Words', `<div class="simple-words-box"><p>${data.in_simple_words}</p></div>`)}

        <!-- ── SECTION 10: DISCLAIMER ── -->
        <div class="report-disclaimer">
            <div class="disclaimer-icon">⚠️</div>
            <p>${data.disclaimer}</p>
        </div>

    </div>`;

    containerEl.innerHTML = html;
    containerEl.classList.remove('hidden');
    // Smooth reveal
    containerEl.style.opacity = '0';
    containerEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(() => {
        containerEl.style.transition = 'opacity 0.5s ease';
        containerEl.style.opacity = '1';
    }, 100);
}

/**
 * Renders an error state inside the result container.
 */
function renderError(containerEl, message) {
    containerEl.innerHTML = `
    <div class="report-error">
        <div class="error-icon">⚠</div>
        <div class="error-title">Connection Error</div>
        <div class="error-message">${message}</div>
    </div>`;
    containerEl.classList.remove('hidden');
}

/* ═══════════════════════════════════════════════════════════════════════════
   FORM SUBMISSION HANDLER
═══════════════════════════════════════════════════════════════════════════ */

async function handleFormSubmit(e, endpoint, dataMapper, resultContainerId) {
    e.preventDefault();

    const submitBtn = e.target.querySelector('button[type="submit"]');
    const origText  = submitBtn.textContent;
    submitBtn.innerHTML = '<div class="loader"></div>';
    submitBtn.disabled  = true;

    const resultCard = document.getElementById(resultContainerId);
    resultCard.classList.add('hidden');
    resultCard.innerHTML = '';

    try {
        const payload  = dataMapper(e.target);
        const response = await fetch(`${API_URL}${API_PREFIX}/predict/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            let errMsg = `Server returned HTTP ${response.status}.`;
            try {
                const errBody = await response.json();
                if (errBody.detail && errBody.detail.message) {
                    errMsg = errBody.detail.message;
                } else if (errBody.detail) {
                    errMsg = typeof errBody.detail === 'string' ? errBody.detail : JSON.stringify(errBody.detail);
                }
            } catch (_) {}
            throw new Error(errMsg);
        }

        const data = await response.json();
        renderMedicalReport(data, resultCard);

    } catch (err) {
        const isNetworkErr = err instanceof TypeError;
        const message = isNetworkErr
            ? `Unable to connect to the backend API at port 5055. Please ensure the server is running:<br><code>uvicorn app.main:app --port 5055 --reload</code>`
            : err.message;
        renderError(resultCard, message);
    } finally {
        submitBtn.textContent = origText;
        submitBtn.disabled    = false;
    }
}

/* ─────────────────────── FORM EVENT LISTENERS ───────────────────────────── */

document.getElementById('form-breast-cancer').addEventListener('submit', (e) => {
    handleFormSubmit(e, 'breast-cancer', () => ({
        mean_radius:     parseFloat(document.getElementById('bc-radius').value),
        mean_texture:    parseFloat(document.getElementById('bc-texture').value),
        mean_perimeter:  parseFloat(document.getElementById('bc-perimeter').value),
        mean_area:       parseFloat(document.getElementById('bc-area').value),
        mean_smoothness: parseFloat(document.getElementById('bc-smoothness').value)
    }), 'result-breast-cancer');
});

document.getElementById('form-diabetes').addEventListener('submit', (e) => {
    handleFormSubmit(e, 'diabetes', () => ({
        pregnancies:    parseFloat(document.getElementById('diab-pregnancies').value),
        glucose:        parseFloat(document.getElementById('diab-glucose').value),
        blood_pressure: parseFloat(document.getElementById('diab-bp').value),
        bmi:            parseFloat(document.getElementById('diab-bmi').value),
        age:            parseFloat(document.getElementById('diab-age').value)
    }), 'result-diabetes');
});

document.getElementById('form-heart-disease').addEventListener('submit', (e) => {
    handleFormSubmit(e, 'heart-disease', () => ({
        age:      parseFloat(document.getElementById('hd-age').value),
        sex:      parseFloat(document.getElementById('hd-sex').value),
        cp:       parseFloat(document.getElementById('hd-cp').value),
        trestbps: parseFloat(document.getElementById('hd-trestbps').value),
        chol:     parseFloat(document.getElementById('hd-chol').value)
    }), 'result-heart-disease');
});
