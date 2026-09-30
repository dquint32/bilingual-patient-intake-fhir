"""Code systems and value sets used by the FHIR builders.

Centralising these removes the long system URLs that were copy-pasted into every
builder function and makes the SNOMED mapping testable on its own.
"""

from __future__ import annotations

from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

SNOMED = "http://snomed.info/sct"
BCP47 = "urn:ietf:bcp:47"
V2_0131 = "http://terminology.hl7.org/CodeSystem/v2-0131"          # contact relationship
V3_ACT_CODE = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
CONDITION_CLINICAL = "http://terminology.hl7.org/CodeSystem/condition-clinical"
CONDITION_VER_STATUS = "http://terminology.hl7.org/CodeSystem/condition-ver-status"
CONDITION_CATEGORY = "http://terminology.hl7.org/CodeSystem/condition-category"
ALLERGY_CLINICAL = "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
ALLERGY_VERIFICATION = "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification"
COVERAGE_CLASS = "http://terminology.hl7.org/CodeSystem/coverage-class"
SUBSCRIBER_RELATIONSHIP = "http://terminology.hl7.org/CodeSystem/subscriber-relationship"
PATIENT_ID_SYSTEM = "http://medintake.example.org/patient-id"


class ConditionKey(StrEnum):
    """Checkbox values sent by the intake form."""

    DIABETES = "diabetes"
    HYPERTENSION = "hypertension"
    ASTHMA = "asthma"


# SNOMED CT concept id -> preferred term
CONDITION_CODES: Mapping[ConditionKey, tuple[str, str]] = MappingProxyType({
    ConditionKey.DIABETES: ("73211009", "Diabetes mellitus"),
    ConditionKey.HYPERTENSION: ("38341003", "Hypertensive disorder, systemic arterial"),
    ConditionKey.ASTHMA: ("195967001", "Asthma"),
})

LANGUAGES: Mapping[str, str] = MappingProxyType({"en": "English", "es": "Spanish"})


def coding(system: str, code: str, display: str | None = None) -> dict:
    out = {"system": system, "code": code}
    if display:
        out["display"] = display
    return out


def concept(system: str, code: str, display: str | None = None, text: str | None = None) -> dict:
    out: dict = {"coding": [coding(system, code, display)]}
    if text:
        out["text"] = text
    return out
