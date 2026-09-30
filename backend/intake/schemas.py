"""Ingestion + validation layer: the request/response contracts.

The original ``/submit`` accepted ``data: dict = Body(...)`` and hand-checked a
list of required keys, so the ``IntakeForm`` model it defined was never used and
malformed emails, impossible dates or unknown conditions went straight into FHIR.
Every request now passes through :class:`IntakeForm` before any FHIR is built.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    computed_field,
    field_validator,
)

from .terminology import ConditionKey

_LIST_SPLIT = re.compile(r"[;,\n]")
_PHONE_CHARS = re.compile(r"^[\d\s().+\-]+$")
_PHONE_IN_TEXT = re.compile(r"\+?\(?\d[\d\s().\-]{8,}\d")

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
OptionalText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


def _check_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if not _PHONE_CHARS.match(value) or not 10 <= len(digits) <= 15:
        raise ValueError("phone number must contain 10-15 digits")
    return value


Phone = Annotated[Text, AfterValidator(_check_phone)]


def split_list(text: str) -> list[str]:
    """'Penicillin, shellfish; latex' -> ['Penicillin', 'shellfish', 'latex'] (deduplicated)."""
    seen: dict[str, str] = {}
    for item in _LIST_SPLIT.split(text):
        item = item.strip()
        if item and item.casefold() not in seen:
            seen[item.casefold()] = item
    return list(seen.values())


class IntakeForm(BaseModel):
    """Payload posted by ``static/js/app.js``."""

    # extra="ignore": the browser's FormData also sends the raw "condition" checkbox key.
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    first_name: Text
    last_name: Text
    email: EmailStr
    dob: date
    phone: Phone
    address: LongText
    emergency_contact: Text
    insurance_provider: Text
    policy_number: Annotated[Text, StringConstraints(max_length=64)]
    reason_for_visit: LongText
    medications: OptionalText = ""
    allergies: OptionalText = ""
    conditions: list[ConditionKey] = Field(default_factory=list)
    language_preference: Literal["en", "es"] = "en"

    @field_validator("dob")
    @classmethod
    def _plausible_dob(cls, v: date) -> date:
        today = date.today()
        if v > today:
            raise ValueError("date of birth cannot be in the future")
        if v.year < today.year - 130:
            raise ValueError("date of birth is more than 130 years ago")
        return v

    @field_validator("conditions", mode="before")
    @classmethod
    def _conditions(cls, v: Any) -> Any:
        if v is None or v == "":
            return []
        if isinstance(v, str):  # a single checkbox can arrive as a bare string
            return [v]
        return v

    @field_validator("conditions")
    @classmethod
    def _dedupe(cls, v: list[ConditionKey]) -> list[ConditionKey]:
        return list(dict.fromkeys(v))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allergy_list(self) -> list[str]:
        return split_list(self.allergies)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def medication_list(self) -> list[str]:
        return split_list(self.medications)

    @property
    def emergency_contact_parts(self) -> tuple[str, str | None]:
        """Split 'John Doe (555) 987-6543' into ('John Doe', '(555) 987-6543')."""
        match = _PHONE_IN_TEXT.search(self.emergency_contact)
        if not match:
            return self.emergency_contact, None
        name = (self.emergency_contact[: match.start()] + self.emergency_contact[match.end():])
        name = re.sub(r"\s{2,}", " ", name).strip(" ,-")
        return name or self.emergency_contact, match.group(0).strip()


class FieldError(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    message: str
    errors: list[FieldError] = Field(default_factory=list)


class SubmitResponse(BaseModel):
    success: Literal[True] = True
    message: str
    timestamp: str
    patient_id: str
    fhir_bundle: dict[str, Any]
