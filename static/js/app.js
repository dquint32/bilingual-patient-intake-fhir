document.addEventListener('DOMContentLoaded', () => {
    // State
    const LANG_KEY = 'medintake-lang';
    const readLang = () => { try { return localStorage.getItem(LANG_KEY); } catch { return null; } };
    const saveLang = lang => { try { localStorage.setItem(LANG_KEY, lang); } catch { /* storage blocked */ } };
    let currentLang = readLang() === 'es' ? 'es' : 'en';
    let lastFhirBundle = null;
    const form = document.getElementById('intake-form');
    const msgBox = document.getElementById('form-message');
    const toggleBtn = document.getElementById('lang-toggle');
    const demoBtn = document.getElementById('demo-data-btn');

    // Where the form is processed.
    // Default: the Python package in backend/intake runs in the browser via Pyodide
    // (see py-engine.js), so the GitHub Pages demo needs no server. Set API_URL to
    // use the FastAPI service instead, e.g. 'http://127.0.0.1:8000/submit'.
    const API_URL = null;
    const engineStatus = document.getElementById('engine-status');
    let engineState = 'loading';
    const engine = window.createPyEngine({
        files: {
            'intake/__init__.py': 'backend/intake/__init__.py',
            'intake/terminology.py': 'backend/intake/terminology.py',
            'intake/schemas.py': 'backend/intake/schemas.py',
            'intake/fhir_builders.py': 'backend/intake/fhir_builders.py',
            'intake/service.py': 'backend/intake/service.py'
        },
        packages: ['pydantic'],
        pipPackages: ['email-validator==2.3.0'],   // required by pydantic.EmailStr
        entry: 'intake.service.submit_json'
    });

    const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));

    function renderEngineStatus() {
        if (!engineStatus) return;
        if (API_URL) { engineStatus.hidden = true; return; }
        const t = translations[currentLang];
        engineStatus.hidden = false;
        engineStatus.dataset.state = engineState;
        const text = { loading: t.engine_loading, ready: t.engine_ready, error: t.engine_error }[engineState];
        engineStatus.innerHTML = `<span class="engine-dot" aria-hidden="true"></span><span>${escapeHtml(text)}</span>`
            + (engineState === 'error'
                ? ` <button type="button" class="link-btn" data-action="retry">${escapeHtml(t.retry)}</button>`
                : '');
    }

    function setEngineState(state) {
        engineState = state;
        renderEngineStatus();
    }

    async function warmUpEngine() {
        setEngineState('loading');
        try {
            await engine.load();
            setEngineState('ready');
        } catch (err) {
            console.error('Python engine failed to load:', err);
            setEngineState('error');
        }
    }

    if (engineStatus) {
        engineStatus.addEventListener('click', e => {
            if (e.target.closest('[data-action="retry"]')) warmUpEngine();
        });
    }

    // Both transports resolve to {status, body} with the same body shape.
    async function submitIntake(data) {
        if (API_URL) {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return { status: response.status, body: await response.json() };
        }
        const out = JSON.parse(await engine.call(JSON.stringify(data)));
        setEngineState('ready');
        return out;
    }

    // Demo data
    const demoData = {
        en: {
            first_name: 'Jane',
            last_name: 'Doe',
            dob: '1985-06-15',
            phone: '(555) 123-4567',
            email: 'jane.doe@example.com',
            address: '123 Main Street, Springfield, IL 62701',
            emergency_contact: 'John Doe (555) 987-6543',
            insurance_provider: 'Blue Cross Blue Shield',
            policy_number: 'BC-789456',
            reason_for_visit: 'Annual checkup and recent fatigue concerns',
            medications: 'Metformin 500mg twice daily, Lisinopril 10mg once daily',
            allergies: 'Penicillin, shellfish',
            conditions: ['diabetes', 'hypertension']
        },
        es: {
            first_name: 'Juan',
            last_name: 'Pérez',
            dob: '1985-06-15',
            phone: '(555) 123-4567',
            email: 'juan.perez@ejemplo.com',
            address: 'Calle Principal 123, Springfield, IL 62701',
            emergency_contact: 'María Pérez (555) 987-6543',
            insurance_provider: 'Blue Cross Blue Shield',
            policy_number: 'BC-789456',
            reason_for_visit: 'Chequeo anual y preocupaciones sobre fatiga reciente',
            medications: 'Metformina 500mg dos veces al día, Lisinopril 10mg una vez al día',
            allergies: 'Penicilina, mariscos',
            conditions: ['diabetes', 'hypertension']
        }
    };

    // --- Language Logic ---
    function updateLanguage() {
        document.documentElement.lang = currentLang;

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (translations[currentLang] && translations[currentLang][key]) {
                el.textContent = translations[currentLang][key];
            }
        });

        document.querySelectorAll('[data-i18n-ph]').forEach(el => {
            const key = el.getAttribute('data-i18n-ph');
            if (translations[currentLang] && translations[currentLang][key]) {
                el.placeholder = translations[currentLang][key];
            }
        });

        renderEngineStatus();

        if (toggleBtn) {
            toggleBtn.setAttribute('aria-label', currentLang === 'en' ? 'Cambiar a español' : 'Switch to English');
        }
    }

    // --- Demo Data Loader ---
    if (demoBtn) {
        demoBtn.addEventListener('click', () => {
            const data = demoData[currentLang];

            document.getElementById('fname').value = data.first_name;
            document.getElementById('lname').value = data.last_name;
            document.getElementById('dob').value = data.dob;
            document.getElementById('phone').value = data.phone;
            document.getElementById('email').value = data.email;
            document.getElementById('address').value = data.address;
            document.getElementById('emergency').value = data.emergency_contact;
            document.getElementById('provider').value = data.insurance_provider;
            document.getElementById('policy').value = data.policy_number;
            document.getElementById('reason').value = data.reason_for_visit;
            document.getElementById('meds').value = data.medications;
            document.getElementById('allergies').value = data.allergies;

            document.querySelectorAll('input[name="condition"]').forEach(checkbox => {
                checkbox.checked = data.conditions.includes(checkbox.value);
            });

            document.querySelectorAll('input, textarea').forEach(el => {
                el.style.borderColor = '';
            });

            msgBox.textContent = translations[currentLang].demo_loaded;
            msgBox.className = 'success-msg';
            setTimeout(() => {
                msgBox.className = 'hidden';
            }, 3000);
        });
    }

    // --- Language Toggle ---
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            currentLang = currentLang === 'en' ? 'es' : 'en';
            saveLang(currentLang);
            updateLanguage();
        });
    }

    // --- FHIR Display Functions ---
    function showFhirPanel(fhirBundle, patientId) {
        const existingPanel = document.getElementById('fhir-panel');
        if (existingPanel) existingPanel.remove();

        const panel = document.createElement('div');
        panel.id = 'fhir-panel';
        panel.className = 'fhir-panel card card-accent';

        const title = currentLang === 'en' ? 'FHIR Resources Generated' : 'Recursos FHIR Generados';
        const closeText = currentLang === 'en' ? 'Close' : 'Cerrar';
        const downloadText = currentLang === 'en' ? 'Download FHIR Bundle' : 'Descargar Bundle FHIR';
        const patientIdText = currentLang === 'en' ? 'Patient ID' : 'ID del Paciente';
        const resourcesText = currentLang === 'en' ? 'Resources Created' : 'Recursos Creados';

        const resourceCount = fhirBundle.entry.length;
        const resourceTypes = fhirBundle.entry.map(e => e.resource.resourceType).join(', ');

        panel.innerHTML = `
            <div class="fhir-header">
                <h3>${title}</h3>
                <button type="button" class="close-fhir icon-btn" aria-label="${closeText}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg></button>
            </div>
            <div class="fhir-content">
                <div class="fhir-summary">
                    <div class="fhir-stat">
                        <span class="stat-label">${patientIdText}:</span>
                        <span class="stat-value">${escapeHtml(patientId)}</span>
                    </div>
                    <div class="fhir-stat">
                        <span class="stat-label">${resourcesText}:</span>
                        <span class="stat-value">${resourceCount} (${escapeHtml(resourceTypes)})</span>
                    </div>
                </div>
                <div class="fhir-actions">
                    <button type="button" id="view-fhir-btn" class="btn btn-secondary" aria-expanded="false" aria-controls="fhir-json">${currentLang === 'en' ? 'View JSON' : 'Ver JSON'}</button>
                    <button type="button" id="download-fhir-btn" class="btn btn-primary">${downloadText}</button>
                </div>
                <pre id="fhir-json" class="fhir-json hidden" tabindex="0" aria-label="FHIR Bundle JSON"></pre>
            </div>
        `;

        document.querySelector('.container').appendChild(panel);

        panel.querySelector('.close-fhir').addEventListener('click', () => panel.remove());

        document.getElementById('view-fhir-btn').addEventListener('click', () => {
            const jsonPre = document.getElementById('fhir-json');
            if (jsonPre.classList.contains('hidden')) {
                jsonPre.textContent = JSON.stringify(fhirBundle, null, 2);
                jsonPre.classList.remove('hidden');
            } else {
                jsonPre.classList.add('hidden');
            }
            document.getElementById('view-fhir-btn').setAttribute('aria-expanded', String(!jsonPre.classList.contains('hidden')));
        });

        document.getElementById('download-fhir-btn').addEventListener('click', () => {
            downloadFhirBundle(fhirBundle, patientId);
        });
    }

    function downloadFhirBundle(bundle, patientId) {
        const dataStr = JSON.stringify(bundle, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `fhir-bundle-${patientId}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    // --- Form Submission ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        msgBox.className = 'hidden';
        document.querySelectorAll('input, textarea').forEach(el => {
            el.style.borderColor = '';
        });

        if (!form.checkValidity()) {
            const requiredFields = form.querySelectorAll('input[required], textarea[required]');

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = 'var(--primary)';
                }
            });

            msgBox.textContent = translations[currentLang].msg_error;
            msgBox.className = 'error-msg';

            const firstInvalid = form.querySelector(':invalid');
            if (firstInvalid) {
                firstInvalid.focus();
            }
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = translations[currentLang].loading;

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const conditions = Array.from(formData.getAll('condition'));
        data.conditions = conditions;
        data.language_preference = currentLang;

        try {
            const { status, body: result } = await submitIntake(data);

            if (status !== 200 || !result.success) {
                const detail = Array.isArray(result.errors) && result.errors.length
                    ? result.errors.map(e => `${e.field}: ${e.message}`).join(' · ')
                    : '';
                // Highlight the inputs the Python validator rejected, like the client-side check does.
                (result.errors || []).forEach(e => {
                    const input = form.querySelector(`[name="${CSS.escape(String(e.field).split('.')[0])}"]`);
                    if (input) input.style.borderColor = 'var(--primary)';
                });
                const err = new Error(result.message || `HTTP ${status}`);
                err.detail = detail;
                err.validation = status === 422;
                throw err;
            }

            form.reset();
            msgBox.textContent = `${result.message} ${result.timestamp}. ${translations[currentLang].fhir_created}`;
            msgBox.className = 'success-msg';

            lastFhirBundle = result.fhir_bundle;
            showFhirPanel(result.fhir_bundle, result.patient_id);
        } catch (error) {
            if (!error.validation) console.error('Submission Error:', error);
            let errorMessage = translations[currentLang].msg_error;

            if (!error.validation) {
                errorMessage = translations[currentLang].conn_error;
                if (!API_URL) setEngineState('error');
            }

            if (error.detail) {
                errorMessage = `${errorMessage} ${error.detail}`;
            }

            msgBox.textContent = errorMessage;
            msgBox.className = 'error-msg';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
        }
    });

    form.addEventListener('input', (e) => {
        if (e.target.style.borderColor === 'var(--primary)') {
            e.target.style.borderColor = '';
        }
    });

    updateLanguage();
    if (!API_URL) warmUpEngine();
});
