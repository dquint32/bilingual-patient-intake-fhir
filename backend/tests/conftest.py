from __future__ import annotations

import itertools
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from intake.api import create_app
from intake.config import Settings
from intake.fhir_builders import BuildContext
from intake.schemas import IntakeForm

# Mirrors the "Load Demo Data" payload in static/js/app.js, including the stray
# "condition" key that the browser's FormData adds.
VALID_PAYLOAD: dict[str, Any] = {
    "first_name": "Jane",
    "last_name": "Doe",
    "dob": "1985-06-15",
    "phone": "(555) 123-4567",
    "email": "jane.doe@example.com",
    "address": "123 Main Street, Springfield, IL 62701",
    "emergency_contact": "John Doe (555) 987-6543",
    "insurance_provider": "Blue Cross Blue Shield",
    "policy_number": "BC-789456",
    "reason_for_visit": "Annual checkup and recent fatigue concerns",
    "medications": "Metformin 500mg twice daily, Lisinopril 10mg once daily",
    "allergies": "Penicillin, shellfish",
    "conditions": ["diabetes", "hypertension"],
    "condition": "hypertension",
    "language_preference": "en",
}


@pytest.fixture
def payload() -> dict[str, Any]:
    return dict(VALID_PAYLOAD)


@pytest.fixture
def form(payload) -> IntakeForm:
    return IntakeForm.model_validate(payload)


@pytest.fixture
def ctx() -> BuildContext:
    """Deterministic clock and IDs so builder output is reproducible."""
    counter = itertools.count(1)
    return BuildContext(
        now=datetime(2026, 1, 15, 9, 30, tzinfo=timezone.utc),
        new_id=lambda: f"00000000-0000-4000-8000-{next(counter):012d}",
    )


@pytest.fixture
def client() -> TestClient:
    app = create_app(Settings(allowed_origins=("https://dquint32.github.io",)))
    return TestClient(app, raise_server_exceptions=False)
