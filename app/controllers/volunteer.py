"""Volunteer controller: pages only volunteers see."""

from __future__ import annotations

from flask import Blueprint, render_template
from flask_login import current_user

from app.auth.roles import role_required
from app.models import RoleName

volunteer_bp = Blueprint("volunteer", __name__, url_prefix="/volunteer")


@volunteer_bp.get("/dashboard")
@role_required(RoleName.VOLUNTEER)
def dashboard() -> str:
    return render_template("volunteer/dashboard.html", user=current_user)
