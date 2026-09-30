# MedIntake: Bilingual Full-Stack Patient Portal

[![tests](https://github.com/dquint32/bilingual-patient-intake-fhir/actions/workflows/tests.yml/badge.svg)](https://github.com/dquint32/bilingual-patient-intake-fhir/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![pydantic](https://img.shields.io/badge/pydantic-v2-e92063)
![FHIR](https://img.shields.io/badge/FHIR-R4-orange)

**Live demo:** https://dquint32.github.io/bilingual-patient-intake-fhir/

## Project Overview
**MedIntake** is a comprehensive patient registration system designed to streamline the data entry process in clinical settings. This project features a responsive frontend and a robust Python backend that processes patient data and maps it to the **HL7 FHIR R4** interoperability standard.

The application addresses the needs of diverse patient populations by providing a seamless, real-time language toggle between English and Spanish.

---

## 🛠 Tech Stack
* **Frontend**: HTML5, CSS3 (Modern Dark Theme), Vanilla JavaScript.
* **Backend**: Python 3.11+, FastAPI.
* **Data Validation**: Pydantic v2. Every request passes through a typed `IntakeForm` model before any FHIR is built.
* **Interoperability**: HL7 FHIR R4 Bundle (Patient, Encounter, Coverage, Condition, AllergyIntolerance, MedicationStatement) with SNOMED CT and BCP-47 coding.
* **Quality**: pytest (69 tests, 100% coverage), GitHub Actions CI on Python 3.11–3.13, bundle structure checked against the official `fhir.resources` R4B models.

---

## ✨ Key Features
* **Bilingual UI**: Instant EN/ES switching of labels, placeholders and messages; the choice is remembered between visits.
* **FHIR Resource Generation**: Maps a flat intake form to a self-contained FHIR R4 Bundle. Every entry has a `urn:uuid` `fullUrl`, and every internal reference resolves within the bundle.
* **Clinically honest mapping**: Patient-reported conditions and allergies are recorded as `unconfirmed` with the patient as asserter. The allergy category is not guessed. The preferred language goes to `Patient.communication`.
* **Strict validation**: Email format, plausible date of birth (not future, not >130 years), 10–15 digit phones, a whitelist of condition codes, and length limits. Errors come back as field-level JSON that the UI displays.
* **Safe error handling**: Malformed JSON returns 422, not 500. Unexpected errors are logged server-side and never echo request data (PHI) to the client.
* **Dynamic Demo Data**: One-click English or Spanish demo profile.

---

## 🏗 System Architecture

```
Browser (index.html + app.js)
   │  POST /submit  (JSON)
   ▼
backend/intake/api.py            HTTP only: routing, CORS, error handlers
   │
   ▼
backend/intake/schemas.py        ingestion + validation: IntakeForm (Pydantic v2)
   │
   ▼
backend/intake/fhir_builders.py  transformation: IntakeForm → FHIR R4 Bundle (pure functions)
backend/intake/terminology.py    SNOMED CT / HL7 code systems in one place
```

### Response contract
```json
{ "success": true, "message": "Intake received successfully.", "timestamp": "2026-01-15 09:30:00 UTC",
  "patient_id": "…uuid…", "fhir_bundle": { "resourceType": "Bundle", "type": "collection", "entry": [ … ] } }
```
Validation failure (HTTP 422):
```json
{ "success": false, "message": "Some fields are missing or invalid.",
  "errors": [ { "field": "dob", "message": "date of birth cannot be in the future" } ] }
```

---

## 📂 Project Structure
* `/` (Root): `index.html`, `Dockerfile`, `fly.toml`.
* `static/css/`: `styles.css` containing the custom UI theme.
* `static/js/`: `app.js` (logic) and `translations.js` (i18n).
* `backend/app.py`: deployment entry point (`uvicorn app:app`).
* `backend/intake/`: the application package (see architecture above).
* `backend/tests/`: pytest suite with mock payloads.

---

## 🎓 Academic Purpose
<section id="purpose">
    <h3>Purpose of This Site</h3>
    <p>This website was created in partial fulfillment of the CIS 3030 course requirements at MSU Denver.</p>
    <dl>
        <dt>Student Developer</dt>
        <dd>David Quintana</dd>
        <dt>Contact</dt>
        <dd>dquint32@msudenver.edu</dd>
        <dt>Language Preference</dt>
        <dd>English | Spanish</dd>
        <dt>Course Info</dt>
        <dd>CIS 3030 - Web Development</dd>
    </dl>
</section>

---

## 🚀 Getting Started

### Backend
```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app:app --reload          # API at http://127.0.0.1:8000, docs at /docs
pytest --cov=intake               # run the test suite
```
Allowed CORS origins default to GitHub Pages and davidquintana.dev. Override them without a code
change: `ALLOWED_ORIGINS="https://example.com,https://other.example"`.

### Docker
```bash
docker build -t medintake .
docker run -p 8080:8080 medintake
```
The container runs as a non-root user and listens on `$PORT` (default 8080), so the same image runs on Railway, Render or Fly.io.

### Frontend
1. Open `index.html` in your browser.
2. The API endpoint is `API_URL` at the top of `static/js/app.js`.

---

**Disclaimer:** This is a portfolio project. While it uses FHIR standards, it is not intended for the storage of real Protected Health Information (PHI) without further security and HIPAA compliance measures.
