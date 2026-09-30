from __future__ import annotations

from collections import Counter

import pytest
from fhir.resources.R4B.bundle import Bundle

from intake.fhir_builders import build_bundle
from intake.schemas import IntakeForm


def resources(bundle: dict, resource_type: str) -> list[dict]:
    return [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == resource_type]


def test_bundle_contains_expected_resources(form, ctx) -> None:
    bundle = build_bundle(form, ctx)
    counts = Counter(e["resource"]["resourceType"] for e in bundle["entry"])
    assert counts == {"Patient": 1, "Encounter": 1, "Coverage": 1, "Condition": 2,
                      "AllergyIntolerance": 2, "MedicationStatement": 2}
    assert bundle["entry"][0]["resource"]["resourceType"] == "Patient"


def test_bundle_validates_against_fhir_r4_schema(form, ctx) -> None:
    """Structure + cardinality check against the official FHIR R4B model classes (fhir.resources)."""
    Bundle.model_validate(build_bundle(form, ctx))


def test_bundle_with_only_required_fields_is_still_valid_fhir(payload, ctx) -> None:
    for key in ("medications", "allergies", "conditions"):
        payload.pop(key)
    bundle = build_bundle(IntakeForm.model_validate(payload), ctx)
    Bundle.model_validate(bundle)
    assert len(bundle["entry"]) == 3


def test_all_references_resolve_inside_the_bundle(form, ctx) -> None:
    bundle = build_bundle(form, ctx)
    full_urls = {e["fullUrl"] for e in bundle["entry"]}

    def walk(node):
        if isinstance(node, dict):
            if "reference" in node:
                yield node["reference"]
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)

    refs = set(walk(bundle))
    assert refs and refs <= full_urls


def test_ids_are_unique_and_timestamps_consistent(form, ctx) -> None:
    bundle = build_bundle(form, ctx)
    ids = [e["resource"]["id"] for e in bundle["entry"]]
    assert len(ids) == len(set(ids))
    stamps = {e["resource"]["meta"]["lastUpdated"] for e in bundle["entry"]}
    assert stamps == {"2026-01-15T09:30:00+00:00"} == {bundle["timestamp"]}


def test_patient_mapping(form, ctx) -> None:
    [patient] = resources(build_bundle(form, ctx), "Patient")
    assert patient["name"][0] == {"use": "official", "family": "Doe", "given": ["Jane"]}
    assert patient["birthDate"] == "1985-06-15"
    assert {t["system"] for t in patient["telecom"]} == {"phone", "email"}
    assert patient["contact"][0]["name"]["text"] == "John Doe"
    assert patient["contact"][0]["telecom"][0]["value"] == "(555) 987-6543"
    assert patient["communication"][0]["language"]["coding"][0]["code"] == "en"


def test_spanish_language_preference_is_recorded(payload, ctx) -> None:
    payload["language_preference"] = "es"
    [patient] = resources(build_bundle(IntakeForm.model_validate(payload), ctx), "Patient")
    coding = patient["communication"][0]["language"]["coding"][0]
    assert (coding["code"], coding["display"]) == ("es", "Spanish")


@pytest.mark.parametrize(("key", "snomed"), [
    ("diabetes", "73211009"), ("hypertension", "38341003"), ("asthma", "195967001"),
])
def test_condition_snomed_codes(payload, ctx, key: str, snomed: str) -> None:
    payload["conditions"] = [key]
    [condition] = resources(build_bundle(IntakeForm.model_validate(payload), ctx), "Condition")
    assert condition["code"]["coding"][0] == {
        "system": "http://snomed.info/sct", "code": snomed,
        "display": condition["code"]["coding"][0]["display"],
    }
    # Patient-reported, so not clinically confirmed.
    assert condition["verificationStatus"]["coding"][0]["code"] == "unconfirmed"


def test_allergies_do_not_guess_a_category(form, ctx) -> None:
    allergies = resources(build_bundle(form, ctx), "AllergyIntolerance")
    assert [a["code"]["text"] for a in allergies] == ["Penicillin", "shellfish"]
    assert all("category" not in a for a in allergies)


def test_medications_are_no_longer_dropped(form, ctx) -> None:
    meds = resources(build_bundle(form, ctx), "MedicationStatement")
    assert [m["medicationCodeableConcept"]["text"] for m in meds] == [
        "Metformin 500mg twice daily", "Lisinopril 10mg once daily"]


def test_coverage_mapping(form, ctx) -> None:
    [coverage] = resources(build_bundle(form, ctx), "Coverage")
    assert coverage["payor"] == [{"display": "Blue Cross Blue Shield"}]
    assert coverage["class"][0]["value"] == "BC-789456"
    assert coverage["relationship"]["coding"][0]["code"] == "self"


def test_unicode_names_survive(payload, ctx) -> None:
    payload.update(first_name="José", last_name="Núñez-Peña")
    bundle = build_bundle(IntakeForm.model_validate(payload), ctx)
    Bundle.model_validate(bundle)
    assert resources(bundle, "Patient")[0]["name"][0]["family"] == "Núñez-Peña"


def _empty_values(node, path="$"):
    """FHIR JSON rule (hl7.org/fhir/R4/json.html): arrays, objects and strings are never empty."""
    if node in ([], {}, "", None):
        yield path
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _empty_values(v, f"{path}[{i}]")
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _empty_values(v, f"{path}.{k}")


@pytest.mark.parametrize("drop", [(), ("medications", "allergies", "conditions")])
def test_bundle_has_no_empty_json_values(payload, ctx, drop) -> None:
    for key in drop:
        payload.pop(key)
    assert list(_empty_values(build_bundle(IntakeForm.model_validate(payload), ctx))) == []
