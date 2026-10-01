from __future__ import annotations

import pytest

import intake.api
import intake.service
from intake.config import DEFAULT_ORIGINS, _origins_from_env


def test_root_and_health(client) -> None:
    assert client.get("/").json()["endpoints"]["submit"] == "/submit (POST)"
    assert client.get("/health").json()["status"] == "healthy"


def test_submit_success_contract_matches_frontend(client, payload) -> None:
    response = client.post("/submit", json=payload)
    assert response.status_code == 200
    body = response.json()
    # Fields read by static/js/app.js
    assert body["success"] is True
    assert body["message"] == "Intake received successfully."
    assert body["timestamp"].endswith("UTC")
    assert body["patient_id"] == body["fhir_bundle"]["entry"][0]["resource"]["id"]
    # PHI is no longer echoed back verbatim.
    assert "received_data" not in body


def test_spanish_message(client, payload) -> None:
    payload["language_preference"] = "es"
    assert client.post("/submit", json=payload).json()["message"] == "Formulario recibido con éxito."


def test_missing_fields_return_field_level_errors(client, payload) -> None:
    del payload["email"]
    payload["dob"] = "2999-01-01"
    response = client.post("/submit", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert {e["field"] for e in body["errors"]} == {"email", "dob"}


@pytest.mark.parametrize("body", ["not json", "[]", "null", "{}"])
def test_malformed_bodies_are_422_not_500(client, body: str) -> None:
    response = client.post("/submit", content=body, headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_unexpected_errors_do_not_leak_details(client, payload, monkeypatch) -> None:
    def boom(*_, **__):
        raise RuntimeError("secret PHI: Jane Doe 1985-06-15")
    monkeypatch.setattr(intake.service, "build_bundle", boom)
    response = client.post("/submit", json=payload)
    assert response.status_code == 500
    assert "Jane" not in response.text and response.json()["message"] == "Internal server error."


def test_cors_allows_configured_origin_only(client, payload) -> None:
    ok = client.options("/submit", headers={
        "Origin": "https://dquint32.github.io", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "https://dquint32.github.io"
    bad = client.options("/submit", headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers


def test_allowed_origins_env_override(monkeypatch) -> None:
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://a.example/, https://b.example")
    assert _origins_from_env() == ("https://a.example", "https://b.example")
    monkeypatch.delenv("ALLOWED_ORIGINS")
    assert _origins_from_env() == DEFAULT_ORIGINS
    assert "https://davidquintana.dev" in DEFAULT_ORIGINS
