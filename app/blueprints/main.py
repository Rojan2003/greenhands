"""Public pages that do not belong to a role: home and health check."""

from __future__ import annotations

from flask import Blueprint, render_template
from sqlalchemy import text

from app.db import SessionLocal

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index() -> str:
    return render_template("index.html")


@main_bp.get("/health")
def health() -> dict[str, str]:
    """Used by CI and deployment checks. Confirms the database answers."""
    SessionLocal.execute(text("SELECT 1"))
    return {"status": "ok"}
