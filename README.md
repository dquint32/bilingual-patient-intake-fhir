# MedIntake: Bilingual Full-Stack Patient Portal

[![tests](https://github.com/dquint32/bilingual-patient-intake-fhir/actions/workflows/tests.yml/badge.svg)](https://github.com/dquint32/bilingual-patient-intake-fhir/actions/workflows/tests.yml)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![pydantic](https://img.shields.io/badge/pydantic-v2-e92063)
![FHIR](https://img.shields.io/badge/FHIR-R4-orange)

**Live demo:** https://dquint32.github.io/bilingual-patient-intake-fhir/

The live demo has no server. It loads [Pyodide](https://pyodide.org) (CPython compiled to WebAssembly) and runs the **same `backend/intake` package the test suite covers**. Your input is validated by the Pydantic v2 models and turned into a FHIR R4 Bundle inside your browser, and nothing is sent anywhere. The same package is also served by FastAPI (Docker, Fly.io, Railway or Render) when a real endpoint is needed.

## Project Overview
**MedIntake** is a comprehensive patient registration system designed to streamline the data entry process in clinical settings. This project features a responsive frontend and a robust Python backend that processes patient data and maps it to the **HL7 FHIR R4** interoperability standard.

The application addresses the needs of diverse patient populations by providing a seamless, real-time language toggle between English and Spanish.

---

## 🛠 Tech Stack
* **Frontend**: HTML5, CSS3 (Modern Dark Theme), Vanilla JavaScript.
* **Backend**: Python 3.11+, FastAPI.
* **Data Validation**: Pydantic v2. Every request passes through a typed `IntakeForm` model before any FHIR is built.
* **Interoperability**: HL7 FHIR R4 Bundle (Patient, Encounter, Coverage, Condition, AllergyIntolerance, MedicationStatement) with SNOMED CT and BCP-47 coding.
* **Quality**: pytest (80 tests, 100% coverage), GitHub Actions CI on Python 3.11–3.13, bundle structure checked against the official `fhir.resources` R4B models.

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
   │  JSON payload
   ├──► static/js/py-engine.js ─► Pyodide ─► intake.service.submit_json   (default: live demo, no server)
   └──► POST /submit ─► backend/intake/api.py (HTTP only: routing, CORS, error handlers)   (optional)
                                   │
                                   ▼
backend/intake/service.py        use case shared by both paths: validate → build bundle → response
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
* `static/css/`: `dq-theme.css` (shared design system, same look as davidquintana.dev, light/dark) and `styles.css` (page layout).
* `static/js/`: `app.js` (logic), `translations.js` (i18n), `py-engine.js` (Pyodide loader that runs `backend/intake` in the browser).
* `backend/app.py`: deployment entry point (`uvicorn app:app`).
* `backend/intake/`: the application package (see architecture above).
* `backend/tests/`: pytest suite with mock payloads.

---

## 🎓 Academic Purpose
Created in partial fulfillment of the CIS 3030 (Web Development) course requirements at MSU Denver.

* **Developer:** David Quintana · [davidquintana.dev](https://davidquintana.dev)
* **Languages:** English | Spanish

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
```bash
python -m http.server 5500        # from the repo root, then open http://localhost:5500
```
The page must be served over HTTP (not opened as `file://`) so it can fetch the `.py` files.
By default the form is processed by Pyodide in the browser. Pydantic ships with Pyodide; `email-validator`, which `EmailStr` needs, is installed from PyPI at load time.
To use the FastAPI backend instead, set `API_URL` at the top of `static/js/app.js` (for example `'http://127.0.0.1:8000/submit'`).

---

**Disclaimer:** This is a portfolio project. While it uses FHIR standards, it is not intended for the storage of real Protected Health Information (PHI) without further security and HIPAA compliance measures.
