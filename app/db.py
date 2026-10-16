"""Database engine and session management.

We use plain SQLAlchemy 2.x (not Flask-SQLAlchemy) so the repositories and services
are ordinary Python code that can be tested without Flask.

- `engine`      : one connection pool for the whole process
- `SessionLocal`: a scoped session, i.e. one Session per request/thread
"""

from __future__ import annotations

from typing import Any

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

SessionLocal: scoped_session[Session] = scoped_session(
    sessionmaker(autoflush=False, expire_on_commit=False)
)


def make_engine(database_url: str, **kwargs: Any) -> Engine:
    """Create an engine. `pool_pre_ping` drops dead connections (XAMPP restarts)."""
    if not database_url:
        msg = "DATABASE_URL is not set. Copy .env.example to .env and fill it in."
        raise RuntimeError(msg)
    return create_engine(database_url, pool_pre_ping=True, future=True, **kwargs)


def init_db(app: Flask, engine: Engine | None = None) -> Engine:
    """Bind the session to an engine and close it at the end of every request."""
    engine = engine or make_engine(app.config["DATABASE_URL"])
    SessionLocal.configure(bind=engine)
    app.extensions["db_engine"] = engine

    @app.teardown_appcontext
    def remove_session(_exc: BaseException | None) -> None:
        SessionLocal.remove()

    return engine
