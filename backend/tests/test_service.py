"""The shared use-case layer: same behaviour for the API and the in-browser demo."""

from __future__ import annotations

import json

import pytest

from intake import service


def test_submit_success_is_deterministic_with_context(payload, ctx) -> None:
    status, body = service.submit(payload, ctx)
    assert status == 200
    assert body["success"] is True
    assert body["timestamp"] == "2026-01-15 09:30:00 UTC"
    assert body["patient_id"] == "00000000-0000-4000-8000-000000000001"
    assert body["fhir_bundle"]["resourceType"] == "Bundle"


def test_submit_spanish_message(payload, ctx) -> None:
    payload["language_preference"] = "es"
    assert service.submit(payload, ctx)[1]["message"] == "Formulario recibido con éxito."


def test_submit_invalid_returns_field_errors(payload) -> None:
    payload["email"] = "not-an-email"
    payload["phone"] = "12"
    status, body = service.submit(payload)
    assert status == 422
    assert body == {
        "success": False,
        "message": service.INVALID_MESSAGE,
        "errors": [
            {"field": "email", "message": body["errors"][0]["message"]},
            {"field": "phone", "message": "phone number must contain 10-15 digits"},
        ],
    }
    assert not body["errors"][1]["message"].startswith("Value error")


@pytest.mark.parametrize("payload", [None, [], "x", 3])
def test_submit_non_object_payload_is_422(payload) -> None:
    status, body = service.submit(payload)
    assert status == 422 and body["errors"][0]["field"] == "body"


def test_submit_json_round_trip(payload) -> None:
    out = json.loads(service.submit_json(json.dumps(payload)))
    assert out["status"] == 200
    assert out["body"]["fhir_bundle"]["entry"][0]["resource"]["resourceType"] == "Patient"


def test_submit_json_malformed_string_is_422() -> None:
    out = json.loads(service.submit_json("{not json"))
    assert out["status"] == 422 and out["body"]["success"] is False


def test_submit_json_keeps_non_ascii(payload) -> None:
    payload["first_name"] = "José"
    payload["language_preference"] = "es"
    raw = service.submit_json(json.dumps(payload))
    assert "José" in raw and "éxito" in raw


def test_api_and_service_agree(client, payload, ctx) -> None:
    api = client.post("/submit", json={**payload, "email": "bad"}).json()
    _, svc = service.submit({**payload, "email": "bad"})
    assert api == svc
