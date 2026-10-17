"""Public pages that do not belong to a role: home and health check (Controller)."""

from __future__ import annotations

from flask import Blueprint, render_template

from app.database import DatabaseManager

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index() -> str:
    return render_template("index.html")


@main_bp.get("/health")
def health() -> dict[str, str]:
    """Used by CI and deployment checks. Raises DatabaseError (503) if MySQL is down."""
    DatabaseManager().ping()
    return {"status": "ok"}
