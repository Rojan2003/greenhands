"""Flask-Login user loader: turns the user id stored in the session cookie into a User."""

from __future__ import annotations

from flask_login import LoginManager

from app.db import SessionLocal
from app.models import User


def register_user_loader(manager: LoginManager) -> None:
    def load_user(user_id: str) -> User | None:
        if not user_id.isdigit():
            return None
        return SessionLocal.get(User, int(user_id))

    # Registered as a plain call (not a decorator) so mypy keeps the function typed.
    manager.user_loader(load_user)
