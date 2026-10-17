"""Flask application factory.

`create_app()` builds and returns a fully configured Flask app. Keeping it in a
function (instead of a global) lets tests create isolated apps with different
settings, and lets `flask --app app run --debug` discover it automatically.

MVC wiring: controllers (app/controllers) are registered here; they call
services, which call DAOs, which use the DatabaseManager singleton.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.database import DatabaseManager
from app.errors import AppError
from app.extensions import csrf, limiter, login_manager
from app.logging_config import configure_logging

log = logging.getLogger(__name__)


def create_app(
    config_object: type[Config] | None = None,
    *,
    overrides: dict[str, Any] | None = None,
) -> Flask:
    """Build the app.

    Args:
        config_object: settings class (defaults to `Config`; tests pass `TestConfig`).
        overrides: extra config values applied last (tests use this).
    """
    configure_logging()

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_object or Config)
    if overrides:
        app.config.update(overrides)

    if not app.config.get("SECRET_KEY"):
        msg = "SECRET_KEY is not set. Copy .env.example to .env and set a random value."
        raise RuntimeError(msg)

    # --- database: one DatabaseManager for the whole app (Singleton) ---
    db = DatabaseManager()
    app.extensions["db_manager"] = db

    @app.teardown_appcontext
    def close_db_connection(_exc: BaseException | None) -> None:
        # Give the thread's connection back at the end of every request.
        db.close()

    # --- extensions ---
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "warning"

    # --- controllers (blueprints) ---
    from app.auth.loader import register_user_loader
    from app.controllers.main import main_bp

    register_user_loader(login_manager)
    app.register_blueprint(main_bp)

    register_error_handlers(app)
    log.info("app created", extra={"action": "startup"})
    return app


def register_error_handlers(app: Flask) -> None:
    """Turn typed service errors and HTTP errors into friendly pages (FR-8)."""

    @app.errorhandler(AppError)
    def handle_app_error(err: AppError) -> tuple[str, int]:
        if err.status_code >= 500:
            log.error("application error: %s", err.message, extra={"action": "app_error"})
        page = render_template("errors/error.html", code=err.status_code, message=err.message)
        return page, err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err: HTTPException) -> tuple[str, int]:
        code = err.code or 500
        return render_template("errors/error.html", code=code, message=err.description), code

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception) -> tuple[str, int]:
        log.exception("unhandled error")
        if app.config.get("TESTING") or app.debug:
            raise err
        return render_template("errors/error.html", code=500, message="Something went wrong."), 500
