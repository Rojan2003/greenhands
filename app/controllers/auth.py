"""Auth controller: login, logout, sign-up (Controller in MVC: thin, no business rules)."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_user, logout_user

from app.errors import AppError
from app.extensions import limiter
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


def _home_for(user: object) -> str:
    """Where a logged-in user lands: admin or volunteer dashboard."""
    is_admin = getattr(user, "is_admin", False)
    return url_for("admin.dashboard") if is_admin else url_for("volunteer.dashboard")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login() -> ResponseReturnValue:
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    if request.method == "GET":
        return render_template("auth/login.html")

    try:
        user = AuthService.build().login(request.form.to_dict())
    except AppError as err:
        flash(err.message, "error")
        return render_template("auth/login.html", username=request.form.get("username", "")), (
            err.status_code if err.status_code != 422 else 200
        )

    login_user(user)
    flash(f"Welcome back, {user.first_name}!", "success")
    next_url = request.args.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(_home_for(user))


@auth_bp.post("/logout")
def logout() -> ResponseReturnValue:
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def signup() -> ResponseReturnValue:
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))
    if request.method == "GET":
        return render_template("auth/signup.html", form={}, errors={})

    form = request.form.to_dict()
    try:
        AuthService.build().register_volunteer(form)
    except AppError as err:
        flash(err.message, "error")
        safe_form = {k: v for k, v in form.items() if "password" not in k}
        return render_template("auth/signup.html", form=safe_form, errors=err.errors), 200

    flash("Your account is ready. Please log in.", "success")
    return redirect(url_for("auth.login"))
