"""Use-case layer shared by the FastAPI app and the in-browser demo (Pyodide).

``submit(payload)`` takes the raw JSON-like dict posted by the form, validates it
with :class:`IntakeForm`, builds the FHIR R4 Bundle, and returns
``(status_code, body)``. The API route and the GitHub Pages demo both go through
this module, so they produce identical responses and identical error messages.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from pydantic import ValidationError

from .fhir_builders import BuildContext, build_bundle
from .schemas import ErrorResponse, FieldError, IntakeForm, SubmitResponse

MESSAGES = {
    "en": "Intake received successfully.",
    "es": "Formulario recibido con éxito.",
}
INVALID_MESSAGE = "Some fields are missing or invalid."


def field_errors(errors: Iterable[dict[str, Any]]) -> list[FieldError]:
    """Pydantic error dicts -> ``[{field, message}]`` the frontend can show next to inputs."""
    return [
        FieldError(
            field=".".join(str(p) for p in err.get("loc", ()) if p != "body") or "body",
            message=str(err.get("msg", "")).removeprefix("Value error, "),
        )
        for err in errors
    ]


def invalid_response(errors: Iterable[dict[str, Any]]) -> ErrorResponse:
    return ErrorResponse(message=INVALID_MESSAGE, errors=field_errors(errors))


def build_submission(form: IntakeForm, ctx: BuildContext | None = None) -> SubmitResponse:
    ctx = ctx or BuildContext()
    bundle = build_bundle(form, ctx)
    return SubmitResponse(
        message=MESSAGES[form.language_preference],
        timestamp=ctx.now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        patient_id=bundle["entry"][0]["resource"]["id"],
        fhir_bundle=bundle,
    )


def submit(payload: Any, ctx: BuildContext | None = None) -> tuple[int, dict[str, Any]]:
    try:
        form = IntakeForm.model_validate(payload)
    except ValidationError as exc:
        return 422, invalid_response(exc.errors()).model_dump(mode="json")
    return 200, build_submission(form, ctx).model_dump(mode="json")


def submit_json(payload_json: str) -> str:
    """String-in/string-out wrapper for the browser bridge (Pyodide)."""
    try:
        payload = json.loads(payload_json)
    except ValueError:
        payload = None
    status, body = submit(payload)
    return json.dumps({"status": status, "body": body}, ensure_ascii=False)
