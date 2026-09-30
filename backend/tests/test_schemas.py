from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from intake.schemas import IntakeForm, split_list
from intake.terminology import ConditionKey


def error_fields(exc: ValidationError) -> set[str]:
    return {str(e["loc"][0]) for e in exc.errors()}


def test_valid_payload_parses(form: IntakeForm) -> None:
    assert form.dob == date(1985, 6, 15)
    assert form.conditions == [ConditionKey.DIABETES, ConditionKey.HYPERTENSION]
    assert form.allergy_list == ["Penicillin", "shellfish"]
    assert form.medication_list == ["Metformin 500mg twice daily", "Lisinopril 10mg once daily"]


@pytest.mark.parametrize("field", [
    "first_name", "last_name", "email", "dob", "phone", "address", "emergency_contact",
    "insurance_provider", "policy_number", "reason_for_visit",
])
def test_every_required_field_is_enforced(payload, field: str) -> None:
    del payload[field]
    with pytest.raises(ValidationError) as exc:
        IntakeForm.model_validate(payload)
    assert field in error_fields(exc.value)


@pytest.mark.parametrize("field", ["first_name", "address", "policy_number"])
def test_whitespace_only_counts_as_missing(payload, field: str) -> None:
    payload[field] = "   "
    with pytest.raises(ValidationError):
        IntakeForm.model_validate(payload)


def test_strings_are_trimmed(payload) -> None:
    payload["first_name"] = "  Jane  "
    assert IntakeForm.model_validate(payload).first_name == "Jane"


@pytest.mark.parametrize(("field", "value"), [
    ("email", "not-an-email"),
    ("dob", "1985-13-40"),
    ("dob", "yesterday"),
    ("dob", (date.today() + timedelta(days=1)).isoformat()),
    ("dob", "1850-01-01"),
    ("phone", "12345"),
    ("phone", "call me maybe"),
    ("language_preference", "fr"),
    ("conditions", ["diabetes", "cancer"]),
    ("first_name", "x" * 201),
    ("policy_number", "P" * 65),
])
def test_invalid_values_are_rejected(payload, field: str, value) -> None:
    payload[field] = value
    with pytest.raises(ValidationError) as exc:
        IntakeForm.model_validate(payload)
    assert field in error_fields(exc.value)


@pytest.mark.parametrize("phone", ["555-123-4567", "+1 (555) 123-4567", "5551234567", "+52 55 1234 5678"])
def test_accepted_phone_formats(payload, phone: str) -> None:
    payload["phone"] = phone
    assert IntakeForm.model_validate(payload).phone == phone


@pytest.mark.parametrize(("raw", "expected"), [
    (None, []), ("", []), ("asthma", [ConditionKey.ASTHMA]),
    (["asthma", "asthma", "diabetes"], [ConditionKey.ASTHMA, ConditionKey.DIABETES]),
])
def test_conditions_normalisation(payload, raw, expected) -> None:
    payload["conditions"] = raw
    assert IntakeForm.model_validate(payload).conditions == expected


def test_optional_fields_default_to_empty(payload) -> None:
    for key in ("medications", "allergies", "conditions", "language_preference"):
        payload.pop(key)
    form = IntakeForm.model_validate(payload)
    assert form.allergy_list == [] and form.medication_list == [] and form.conditions == []
    assert form.language_preference == "en"


@pytest.mark.parametrize(("text", "expected"), [
    ("Penicillin, shellfish; latex", ["Penicillin", "shellfish", "latex"]),
    ("Penicillin\nPENICILLIN, ,", ["Penicillin"]),
    ("  ", []),
])
def test_split_list(text: str, expected: list[str]) -> None:
    assert split_list(text) == expected


@pytest.mark.parametrize(("text", "name", "phone"), [
    ("John Doe (555) 987-6543", "John Doe", "(555) 987-6543"),
    ("María Pérez - 555.987.6543", "María Pérez", "555.987.6543"),
    ("John Doe", "John Doe", None),
    ("(555) 987-6543", "(555) 987-6543", "(555) 987-6543"),
])
def test_emergency_contact_is_split_into_name_and_phone(payload, text, name, phone) -> None:
    payload["emergency_contact"] = text
    assert IntakeForm.model_validate(payload).emergency_contact_parts == (name, phone)
