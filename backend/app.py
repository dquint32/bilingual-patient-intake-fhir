from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import uuid

app = FastAPI(title="Healthcare Intake API", version="1.0.0")

# CORS Configuration - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for data validation
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

def convert_to_fhir_patient(data: dict) -> dict:
    """
    Converts intake form data to FHIR R4 Patient resource format.
    FHIR Spec: https://www.hl7.org/fhir/patient.html
    """
    patient_id = str(uuid.uuid4())
    
    # Build name array
    name_obj = {
        "use": "official",
        "family": data.get("last_name", ""),
        "given": [data.get("first_name", "")]
    }
    
    # Build telecom array (phone and email)
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
    
    # Build address
    address = []
    if data.get("address"):
        address.append({
            "use": "home",
            "type": "physical",
            "text": data.get("address")
        })
    
    # Build contact (emergency contact)
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
            "name": {
                "text": data.get("emergency_contact")
            }
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
    """
    Converts visit information to FHIR R4 Encounter resource.
    FHIR Spec: https://www.hl7.org/fhir/encounter.html
    """
    encounter_id = str(uuid.uuid4())
    
    fhir_encounter = {
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
    
    return fhir_encounter

def convert_to_fhir_condition(data: dict, patient_id: str) -> list:
    """
    Converts health conditions to FHIR R4 Condition resources.
    FHIR Spec: https://www.hl7.org/fhir/condition.html
    """
    conditions = data.get("conditions", [])
    fhir_conditions = []
    
    # SNOMED CT codes for common conditions
    condition_codes = {
        "diabetes": {"code": "73211009", "display": "Diabetes mellitus"},
        "hypertension": {"code": "38341003", "display": "Hypertension"},
        "asthma": {"code": "195967001", "display": "Asthma"}
    }
    
    for condition in conditions:
        if condition in condition_codes:
            condition_id = str(uuid.uuid4())
            code_info = condition_codes[condition]
            
            fhir_condition = {
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
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "recordedDate": datetime.now().isoformat() + "Z"
            }
            
            fhir_conditions.append(fhir_condition)
    
    return fhir_conditions

def convert_to_fhir_allergy(data: dict, patient_id: str) -> list:
    """
    Converts allergies to FHIR R4 AllergyIntolerance resources.
    FHIR Spec: https://www.hl7.org/fhir/allergyintolerance.html
    """
    allergies_text = data.get("allergies", "").strip()
    if not allergies_text:
        return []
    
    # Split by common delimiters
    allergy_list = [a.strip() for a in allergies_text.replace(',', ';').split(';') if a.strip()]
    fhir_allergies = []
    
    for allergy in allergy_list:
        allergy_id = str(uuid.uuid4())
        
        fhir_allergy = {
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
            "patient": {
                "reference": f"Patient/{patient_id}"
            },
            "recordedDate": datetime.now().isoformat() + "Z",
            "code": {
                "text": allergy
            }
        }
        
        fhir_allergies.append(fhir_allergy)
    
    return fhir_allergies

def convert_to_fhir_coverage(data: dict, patient_id: str) -> dict:
    """
    Converts insurance info to FHIR R4 Coverage resource.
    FHIR Spec: https://www.hl7.org/fhir/coverage.html
    """
    coverage_id = str(uuid.uuid4())
    
    fhir_coverage = {
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
        "subscriber": {
            "reference": f"Patient/{patient_id}"
        },
        "beneficiary": {
            "reference": f"Patient/{patient_id}"
        },
        "payor": [{
            "display": data.get("insurance_provider", "Unknown Insurance")
        }],
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
    
    return fhir_coverage

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "Healthcare API Active - FHIR Enabled",
        "version": "1.0.0",
        "endpoints": {
            "submit": "/submit (POST)"
        }
    }

@app.post("/submit")
def submit_form(data: dict = Body(...)):
    """
    Receives form JSON, converts to FHIR format,
    and returns confirmation with FHIR resources.
    """
    try:
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'dob', 'phone', 
                          'address', 'emergency_contact', 'insurance_provider', 
                          'policy_number', 'reason_for_visit']
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lang = data.get("language_preference", "en")
        
        # Convert to FHIR
        fhir_patient = convert_to_fhir_patient(data)
        patient_id = fhir_patient["id"]
        
        fhir_encounter = convert_to_fhir_encounter(data, patient_id)
        fhir_conditions = convert_to_fhir_condition(data, patient_id)
        fhir_allergies = convert_to_fhir_allergy(data, patient_id)
        fhir_coverage = convert_to_fhir_coverage(data, patient_id)
        
        # Build FHIR Bundle (collection of resources)
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
        
        # Add conditions if present
        for condition in fhir_conditions:
            fhir_bundle["entry"].append({"resource": condition})
        
        # Add allergies if present
        for allergy in fhir_allergies:
            fhir_bundle["entry"].append({"resource": allergy})
        
        # Mock Database Logic
        print(f"\n{'='*60}")
        print(f"INTAKE RECEIVED")
        print(f"{'='*60}")
        print(f"Patient: {data.get('first_name')} {data.get('last_name')}")
        print(f"Email: {data.get('email')}")
        print(f"FHIR Patient ID: {patient_id}")
        print(f"Resources Generated: {len(fhir_bundle['entry'])}")
        print(f"{'='*60}\n")
        
        # Bilingual Response
        if lang == "es":
            message = "Formulario recibido con éxito. "
        else:
            message = "Intake received successfully. "
        
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
        print(f"Error processing submission: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# To run locally: 
# cd backend
# python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```