"""HTTP layer: routing, CORS and error handling only. No FHIR logic lives here."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings, get_settings
from .fhir_builders import BuildContext, build_bundle
from .schemas import ErrorResponse, FieldError, IntakeForm, SubmitResponse

logger = logging.getLogger("intake")

MESSAGES = {
    "en": "Intake received successfully.",
    "es": "Formulario recibido con éxito.",
}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,  # the frontend sends no cookies/auth
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            FieldError(
                field=".".join(str(p) for p in err["loc"] if p != "body") or "body",
                message=str(err["msg"]).removeprefix("Value error, "),
            )
            for err in exc.errors()
        ]
        body = ErrorResponse(message="Some fields are missing or invalid.", errors=errors)
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        # Log server-side; never echo exception text (which may contain PHI) to the client.
        logger.exception("Unhandled error while processing intake")
        return JSONResponse(status_code=500,
                            content=ErrorResponse(message="Internal server error.").model_dump())

    @app.get("/")
    def root() -> dict:
        return {
            "status": "Healthcare API Active - FHIR Enabled",
            "version": settings.version,
            "endpoints": {"submit": "/submit (POST)", "health": "/health", "docs": "/docs"},
        }

    @app.get("/health")
    def health() -> dict:
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

    @app.post("/submit", response_model=SubmitResponse,
              responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
    def submit(form: IntakeForm) -> SubmitResponse:
        ctx = BuildContext()
        bundle = build_bundle(form, ctx)
        return SubmitResponse(
            message=MESSAGES[form.language_preference],
            timestamp=ctx.now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            patient_id=bundle["entry"][0]["resource"]["id"],
            fhir_bundle=bundle,
        )

    return app


app = create_app()
