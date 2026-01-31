from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import uuid

app = FastAPI(title="Healthcare Intake API", version="1.0.0")

# ---------------------------------------------------------
# CORS CONFIGURATION (FIXED)
# ---------------------------------------------------------
# IMPORTANT:
# - Removed "*" wildcard (breaks CORS with credentials)
# - Added ONLY your GitHub Pages frontend origins
# - This is the correct configuration for Railway + GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dquint32.github.io",
        "https://dquint32.github.io/bilingual-patient-intake-fhir"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# DATA MODEL
# ---------------------------------------------------------
class IntakeForm(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    dob: str
    phone: str
    address: str
    emergency_contact: str
    insurance_provider: str
    policy_number: str
    reason_for_visit: str
    medications: Optional[str] = ""
    allergies: Optional[str] = ""
    conditions: Optional[List[str]] = []
    language_preference: str = "en"

# ---------------------------------------------------------
# FHIR GENERATION FUNCTIONS
# ---------------------------------------------------------
def convert_to_fhir_patient(data: dict) -> dict:
    patient_id = str(uuid.uuid4())

    name_obj = {
        "use": "official",
        "family": data.get("last_name", ""),
        "given": [data.get("first_name", "")]
    }

    telecom = []
    if data.get("phone"):
        telecom.append({
            "system": "phone",
            "value": data.get("phone"),
            "use": "mobile"
        })
    if data.get("email"):
        telecom.append({
            "system": "email",
            "value": data.get("email")
        })

    address = []
    if data.get("address"):
        address.append({
            "use": "home",
            "type": "physical",
            "text": data.get("address")
        })

    contact = []
    if data.get("emergency_contact"):
        contact.append({
            "relationship": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                    "code": "C",
                    "display": "Emergency Contact"
                }]
            }],
            "name": {"text": data.get("emergency_contact")}
        })

    fhir_patient = {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {
            "versionId": "1",
            "lastUpdated": datetime.now().isoformat() + "Z"
        },
        "identifier": [{
            "system": "http://medintake.example.org/patient-id",
            "value": patient_id
        }],
        "active": True,
        "name": [name_obj],
        "telecom": telecom,
        "birthDate": data.get("dob", ""),
        "address": address,
        "contact": contact
    }

    return fhir_patient


def convert_to_fhir_encounter(data: dict, patient_id: str) -> dict:
    encounter_id = str(uuid.uuid4())

    return {
        "resourceType": "Encounter",
        "id": encounter_id,
        "meta": {
            "versionId": "1",
            "lastUpdated": datetime.now().isoformat() + "Z"
        },
        "status": "planned",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory"
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
            "display": f"{data.get('first_name')} {data.get('last_name')}"
        },
        "reasonCode": [{
            "text": data.get("reason_for_visit", "General consultation")
        }]
    }


def convert_to_fhir_condition(data: dict, patient_id: str) -> list:
    conditions = data.get("conditions", [])
    fhir_conditions = []

    condition_codes = {
        "diabetes": {"code": "73211009", "display": "Diabetes mellitus"},
        "hypertension": {"code": "38341003", "display": "Hypertension"},
        "asthma": {"code": "195967001", "display": "Asthma"}
    }

    for condition in conditions:
        if condition in condition_codes:
            condition_id = str(uuid.uuid4())
            code_info = condition_codes[condition]

            fhir_conditions.append({
                "resourceType": "Condition",
                "id": condition_id,
                "meta": {
                    "versionId": "1",
                    "lastUpdated": datetime.now().isoformat() + "Z"
                },
                "clinicalStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                        "display": "Active"
                    }]
                },
                "verificationStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                        "display": "Confirmed"
                    }]
                },
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": code_info["code"],
                        "display": code_info["display"]
                    }],
                    "text": code_info["display"]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "recordedDate": datetime.now().isoformat() + "Z"
            })

    return fhir_conditions


def convert_to_fhir_allergy(data: dict, patient_id: str) -> list:
    allergies_text = data.get("allergies", "").strip()
    if not allergies_text:
        return []

    allergy_list = [a.strip() for a in allergies_text.replace(',', ';').split(';') if a.strip()]
    fhir_allergies = []

    for allergy in allergy_list:
        allergy_id = str(uuid.uuid4())

        fhir_allergies.append({
            "resourceType": "AllergyIntolerance",
            "id": allergy_id,
            "meta": {
                "versionId": "1",
                "lastUpdated": datetime.now().isoformat() + "Z"
            },
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                    "code": "active",
                    "display": "Active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                    "code": "confirmed",
                    "display": "Confirmed"
                }]
            },
            "type": "allergy",
            "category": ["medication"],
            "patient": {"reference": f"Patient/{patient_id}"},
            "recordedDate": datetime.now().isoformat() + "Z",
            "code": {"text": allergy}
        })

    return fhir_allergies


def convert_to_fhir_coverage(data: dict, patient_id: str) -> dict:
    coverage_id = str(uuid.uuid4())

    return {
        "resourceType": "Coverage",
        "id": coverage_id,
        "meta": {
            "versionId": "1",
            "lastUpdated": datetime.now().isoformat() + "Z"
        },
        "status": "active",
        "type": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "HIP",
                "display": "health insurance plan policy"
            }]
        },
        "subscriber": {"reference": f"Patient/{patient_id}"},
        "beneficiary": {"reference": f"Patient/{patient_id}"},
        "payor": [{"display": data.get("insurance_provider", "Unknown Insurance")}],
        "class": [{
            "type": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/coverage-class",
                    "code": "policy",
                    "display": "Policy"
                }]
            },
            "value": data.get("policy_number", ""),
            "name": data.get("insurance_provider", "")
        }]
    }

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------
@app.get("/")
def read_root():
    return {
        "status": "Healthcare API Active - FHIR Enabled",
        "version": "1.0.0",
        "endpoints": {"submit": "/submit (POST)"}
    }


@app.post("/submit")
def submit_form(data: dict = Body(...)):
    try:
        required_fields = [
            'first_name', 'last_name', 'email', 'dob', 'phone',
            'address', 'emergency_contact', 'insurance_provider',
            'policy_number', 'reason_for_visit'
        ]

        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lang = data.get("language_preference", "en")

        fhir_patient = convert_to_fhir_patient(data)
        patient_id = fhir_patient["id"]

        fhir_encounter = convert_to_fhir_encounter(data, patient_id)
        fhir_conditions = convert_to_fhir_condition(data, patient_id)
        fhir_allergies = convert_to_fhir_allergy(data, patient_id)
        fhir_coverage = convert_to_fhir_coverage(data, patient_id)

        fhir_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "timestamp": datetime.now().isoformat() + "Z",
            "entry": [
                {"resource": fhir_patient},
                {"resource": fhir_encounter},
                {"resource": fhir_coverage}
            ]
        }

        for condition in fhir_conditions:
            fhir_bundle["entry"].append({"resource": condition})

        for allergy in fhir_allergies:
            fhir_bundle["entry"].append({"resource": allergy})

        if lang == "es":
            message = "Formulario recibido con éxito."
        else:
            message = "Intake received successfully."

        return {
            "success": True,
            "message": message,
            "timestamp": timestamp,
            "patient_id": patient_id,
            "fhir_bundle": fhir_bundle,
            "received_data": data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
