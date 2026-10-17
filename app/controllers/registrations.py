"""Registrations controller: a volunteer's own registrations, schedule and cancel.

Thin by design (Controller in MVC): read the request, call
MyRegistrationsService, pick a template or redirect. Every route is
VOLUNTEER-only (`role_required`), and the service checks the role again and
only ever touches the logged-in volunteer's own rows (FR-2).
"""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user

from app.auth.roles import role_required
from app.errors import ConflictError
from app.models import RegistrationStatus, RoleName
from app.services.my_registrations_service import MyRegistrationsService

registrations_bp = Blueprint("registrations", __name__, url_prefix="/registrations")

TABS = [("", "All")] + [(s.value, s.value.capitalize()) for s in RegistrationStatus]


def _status_filter(raw: str | None) -> RegistrationStatus | None:
    """?status=pending -> PENDING; blank or unknown means every status."""
    try:
        return RegistrationStatus(str(raw or "").strip().upper())
    except ValueError:
        return None


@registrations_bp.get("")  # exactly "/registrations"
@role_required(RoleName.VOLUNTEER)
def list_registrations() -> ResponseReturnValue:
    status = _status_filter(request.args.get("status"))
    mine = MyRegistrationsService.build().list_mine(current_user, status)
    return render_template(
        "volunteer/registrations/list.html",
        mine=mine,
        status_filter=status.value if status else "",
        tabs=TABS,
    )


@registrations_bp.get("/schedule")
@role_required(RoleName.VOLUNTEER)
def schedule() -> ResponseReturnValue:
    plan = MyRegistrationsService.build().schedule(current_user)
    return render_template("volunteer/registrations/schedule.html", schedule=plan)


@registrations_bp.post("/<int:registration_id>/cancel")
@role_required(RoleName.VOLUNTEER)
def cancel(registration_id: int) -> ResponseReturnValue:
    """Cancel one of the volunteer's own registrations; back to the list they came from."""
    back = redirect(
        url_for("registrations.list_registrations", status=request.args.get("status") or None)
    )
    try:
        registration = MyRegistrationsService.build().cancel(current_user, registration_id)
    except ConflictError as err:
        flash(err.message, "error")
        return back
    flash(
        f"Your registration for {registration.activity_title} has been cancelled. "
        "You can register again while the activity is open.",
        "success",
    )
    return back
