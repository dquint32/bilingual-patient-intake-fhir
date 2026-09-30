"""Bilingual patient intake -> FHIR R4 service.

Layers:
    schemas.py        ingestion + validation (Pydantic v2 request/response contracts)
    fhir_builders.py  transformation (IntakeForm -> FHIR R4 Bundle), framework-free
    terminology.py    code systems and the SNOMED CT condition map
    api.py            FastAPI routing, CORS, error handling
"""
