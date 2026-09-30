"""Deployment entry point: ``uvicorn app:app`` (used by the Dockerfile).

All logic lives in the ``intake`` package; see intake/__init__.py for the layout.
"""

from intake.api import app

__all__ = ["app"]
