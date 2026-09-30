"""Transformation layer: validated IntakeForm -> FHIR R4 resources.

Pure functions with no FastAPI dependency, so they can be unit-tested directly.
Compared with the original:

* one shared ``BuildContext`` supplies the timestamp and ID factory, replacing
  eight separate ``datetime.now().isoformat() + "Z"`` calls (which stamped *local*
  time with a UTC "Z" suffix and gave each resource a slightly different time);
* repeated ``meta``/``coding`` dictionaries come from small helpers;
* bundle entries carry ``fullUrl: urn:uuid:...`` and resources reference each
  other by that URN, so the bundle resolves on its own;
* patient-reported data is marked ``unconfirmed`` and asserted by the patient
  instead of being labelled clinically ``confirmed``;
* allergies no longer default to ``category: medication``. "Shellfish" is a food,
  and the form cannot tell us the category;
* medications, which the form collected and then silently dropped, are now
  emitted as ``MedicationStatement`` resources;
* the patient's language preference is recorded in ``Patient.communication``.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from . import terminology as t
from .schemas import IntakeForm

Resource = dict[str, Any]


@dataclass(frozen=True)
class BuildContext:
    now: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    new_id: Callable[[], str] = field(default=lambda: str(uuid.uuid4()))

    @property
    def instant(self) -> str:
        return self.now.isoformat(timespec="seconds")


def _base(resource_type: str, ctx: BuildContext) -> Resource:
    return {
        "resourceType": resource_type,
        "id": ctx.new_id(),
        "meta": {"versionId": "1", "lastUpdated": ctx.instant},
    }


def ref(resource: Resource, display: str | None = None) -> dict:
    out = {"reference": f"urn:uuid:{resource['id']}"}
    if display:
        out["display"] = display
    return out


# --------------------------------------------------------------------------- resources

def build_patient(form: IntakeForm, ctx: BuildContext) -> Resource:
    patient = _base("Patient", ctx)
    contact_name, contact_phone = form.emergency_contact_parts
    contact: dict[str, Any] = {
        "relationship": [t.concept(t.V2_0131, "C", "Emergency Contact")],
        "name": {"text": contact_name},
    }
    if contact_phone:
        contact["telecom"] = [{"system": "phone", "value": contact_phone}]

    patient.update({
        "identifier": [{"system": t.PATIENT_ID_SYSTEM, "value": patient["id"]}],
        "active": True,
        "name": [{"use": "official", "family": form.last_name, "given": [form.first_name]}],
        "telecom": [
            {"system": "phone", "value": form.phone, "use": "mobile"},
            {"system": "email", "value": str(form.email)},
        ],
        "birthDate": form.dob.isoformat(),
        "address": [{"use": "home", "type": "physical", "text": form.address}],
        "contact": [contact],
        "communication": [{
            "language": t.concept(t.BCP47, form.language_preference,
                                  t.LANGUAGES[form.language_preference]),
            "preferred": True,
        }],
    })
    return patient


def build_encounter(form: IntakeForm, patient: Resource, ctx: BuildContext) -> Resource:
    encounter = _base("Encounter", ctx)
    encounter.update({
        "status": "planned",
        "class": t.coding(t.V3_ACT_CODE, "AMB", "ambulatory"),
        "subject": ref(patient, f"{form.first_name} {form.last_name}"),
        "reasonCode": [{"text": form.reason_for_visit}],
    })
    return encounter


def build_conditions(form: IntakeForm, patient: Resource, ctx: BuildContext) -> list[Resource]:
    resources = []
    for key in form.conditions:
        code, display = t.CONDITION_CODES[key]
        condition = _base("Condition", ctx)
        condition.update({
            "clinicalStatus": t.concept(t.CONDITION_CLINICAL, "active", "Active"),
            "verificationStatus": t.concept(t.CONDITION_VER_STATUS, "unconfirmed", "Unconfirmed"),
            "category": [t.concept(t.CONDITION_CATEGORY, "problem-list-item", "Problem List Item")],
            "code": t.concept(t.SNOMED, code, display, text=display),
            "subject": ref(patient),
            "asserter": ref(patient),
            "recordedDate": ctx.instant,
        })
        resources.append(condition)
    return resources


def build_allergies(form: IntakeForm, patient: Resource, ctx: BuildContext) -> list[Resource]:
    resources = []
    for substance in form.allergy_list:
        allergy = _base("AllergyIntolerance", ctx)
        allergy.update({
            "clinicalStatus": t.concept(t.ALLERGY_CLINICAL, "active", "Active"),
            "verificationStatus": t.concept(t.ALLERGY_VERIFICATION, "unconfirmed", "Unconfirmed"),
            "code": {"text": substance},
            "patient": ref(patient),
            "asserter": ref(patient),
            "recordedDate": ctx.instant,
        })
        resources.append(allergy)
    return resources


def build_medications(form: IntakeForm, patient: Resource, ctx: BuildContext) -> list[Resource]:
    resources = []
    for medication in form.medication_list:
        statement = _base("MedicationStatement", ctx)
        statement.update({
            "status": "active",
            "medicationCodeableConcept": {"text": medication},
            "subject": ref(patient),
            "informationSource": ref(patient),
            "dateAsserted": ctx.instant,
        })
        resources.append(statement)
    return resources


def build_coverage(form: IntakeForm, patient: Resource, ctx: BuildContext) -> Resource:
    coverage = _base("Coverage", ctx)
    coverage.update({
        "status": "active",
        "type": t.concept(t.V3_ACT_CODE, "HIP", "health insurance plan policy"),
        "subscriber": ref(patient),
        "beneficiary": ref(patient),
        "relationship": t.concept(t.SUBSCRIBER_RELATIONSHIP, "self", "Self"),
        "payor": [{"display": form.insurance_provider}],
        "class": [{
            "type": t.concept(t.COVERAGE_CLASS, "policy", "Policy"),
            "value": form.policy_number,
            "name": form.insurance_provider,
        }],
    })
    return coverage


def build_bundle(form: IntakeForm, ctx: BuildContext | None = None) -> Resource:
    """Assemble every resource for one intake submission into a FHIR R4 Bundle."""
    ctx = ctx or BuildContext()
    patient = build_patient(form, ctx)
    resources = [
        patient,
        build_encounter(form, patient, ctx),
        build_coverage(form, patient, ctx),
        *build_conditions(form, patient, ctx),
        *build_allergies(form, patient, ctx),
        *build_medications(form, patient, ctx),
    ]
    return {
        "resourceType": "Bundle",
        "id": ctx.new_id(),
        "type": "collection",
        "timestamp": ctx.instant,
        "entry": [{"fullUrl": f"urn:uuid:{r['id']}", "resource": r} for r in resources],
    }
