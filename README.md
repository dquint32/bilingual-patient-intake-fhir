# MedIntake: Bilingual Full-Stack Patient Portal

## Project Overview
**MedIntake** is a comprehensive patient registration system designed to streamline the data entry process in clinical settings. This project features a responsive frontend and a robust Python backend that processes patient data and maps it to the **HL7 FHIR R4** interoperability standard.

The application addresses the needs of diverse patient populations by providing a seamless, real-time language toggle between English and Spanish.

---

## 🛠 Tech Stack
* **Frontend**: HTML5, CSS3 (Modern Dark Theme), Vanilla JavaScript.
* **Backend**: Python 3.x, FastAPI (High-performance web framework).
* **Data Validation**: Pydantic (Strongly-typed data models).
* **Interoperability**: HL7 FHIR R4 Mapping logic.

---

## ✨ Key Features
* **Bilingual UI**: Instant translation of all labels, placeholders, and error messages using a modular `translations.js` system.
* **FHIR Resource Generation**: The backend automatically generates a unique Patient UUID and formats data into a FHIR-compliant Bundle.
* **Dynamic Demo Data**: One-click "Load Demo Data" button to demonstrate system capabilities for both English and Spanish profiles.
* **Responsive Design**: Mobile-first architecture with a high-contrast medical "Dark Mode" aesthetic.
* **Form Validation**: Real-time feedback for required fields and specific email/phone formatting.

---

## 🏗 System Architecture


[Image of Web Application Architecture diagram]

1. **Frontend**: Captures demographics, insurance, and medical history.
2. **API (FastAPI)**: Receives JSON data via POST request.
3. **FHIR Engine**: Logic inside `app.py` transforms flat JSON into nested FHIR R4 resources.
4. **Response**: Returns a success confirmation and the raw FHIR JSON to the user.

---

## 📂 Project Structure
* `/` (Root): `index.html` and project configuration.
* `static/css/`: `styles.css` containing the custom UI theme.
* `static/js/`: `app.js` (logic) and `translations.js` (i18n).
* `backend/`: `app.py` (FastAPI Server) and `requirements.txt`.

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

### Backend Setup
1. Navigate to the backend folder: `cd backend`
2. Install dependencies: `pip install -r requirements.txt`
3. Start the server: `uvicorn app:app --reload`

### Frontend Setup
1. Simply open `index.html` in your browser.
2. Ensure the backend is running to enable the "Submit" and "FHIR Generation" features.

---

**Disclaimer:** This is a portfolio project. While it uses FHIR standards, it is not intended for the storage of real Protected Health Information (PHI) without further security and HIPAA compliance measures.
