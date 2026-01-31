document.addEventListener('DOMContentLoaded', () => {
    // State
    let currentLang = 'en';
    let lastFhirBundle = null;
    const form = document.getElementById('intake-form');
    const msgBox = document.getElementById('form-message');
    const toggleBtn = document.getElementById('lang-toggle');
    const toggleSpan = document.getElementById('lang-span');
    const demoBtn = document.getElementById('demo-data-btn');

    // Backend URL (UPDATED)
    const API_URL = 'https://app-holy-flower-295-production.up.railway.app/submit';

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

        if (toggleSpan && translations[currentLang]) {
            toggleSpan.textContent = translations[currentLang].toggle_label;
            toggleSpan.setAttribute('lang', currentLang === 'en' ? 'es' : 'en');
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
            updateLanguage();
        });
    }

    // --- FHIR Display Functions ---
    function showFhirPanel(fhirBundle, patientId) {
        const existingPanel = document.getElementById('fhir-panel');
        if (existingPanel) existingPanel.remove();

        const panel = document.createElement('div');
        panel.id = 'fhir-panel';
        panel.className = 'fhir-panel';

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
                <button class="close-fhir" aria-label="${closeText}">×</button>
            </div>
            <div class="fhir-content">
                <div class="fhir-summary">
                    <div class="fhir-stat">
                        <span class="stat-label">${patientIdText}:</span>
                        <span class="stat-value">${patientId}</span>
                    </div>
                    <div class="fhir-stat">
                        <span class="stat-label">${resourcesText}:</span>
                        <span class="stat-value">${resourceCount} (${resourceTypes})</span>
                    </div>
                </div>
                <div class="fhir-actions">
                    <button id="view-fhir-btn" class="btn-outline">${currentLang === 'en' ? 'View JSON' : 'Ver JSON'}</button>
                    <button id="download-fhir-btn" class="btn-primary">${downloadText}</button>
                </div>
                <pre id="fhir-json" class="fhir-json hidden"></pre>
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
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                form.reset();

                const successText = result.message + result.timestamp;
                const fhirText = currentLang === 'en'
                    ? ' FHIR resources created successfully.'
                    : ' Recursos FHIR creados exitosamente.';

                msgBox.textContent = successText + fhirText;
                msgBox.className = 'success-msg';

                lastFhirBundle = result.fhir_bundle;
                showFhirPanel(result.fhir_bundle, result.patient_id);

            } else {
                throw new Error(result.message || 'Server error');
            }
        } catch (error) {
            console.error('Submission Error:', error);
            let errorMessage = translations[currentLang].msg_error;

            if (error.message.includes('Failed to fetch')) {
                errorMessage = currentLang === 'en'
                    ? 'Cannot connect to server. Please try again later.'
                    : 'No se puede conectar al servidor. Inténtelo de nuevo más tarde.';
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
});
