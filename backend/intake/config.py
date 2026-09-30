"""Runtime settings, overridable with environment variables (no code change to redeploy)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_ORIGINS = (
    "https://dquint32.github.io",
    "https://davidquintana.dev",
    "https://www.davidquintana.dev",
)


def _origins_from_env() -> tuple[str, ...]:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    # CORS origins are scheme://host[:port] only; a path (as in the original config) never matches.
    parsed = tuple(o.strip().rstrip("/") for o in raw.split(",") if o.strip())
    return parsed or DEFAULT_ORIGINS


@dataclass(frozen=True)
class Settings:
    app_name: str = "Healthcare Intake API"
    version: str = "2.0.0"
    allowed_origins: tuple[str, ...] = field(default_factory=_origins_from_env)


def get_settings() -> Settings:
    return Settings()
