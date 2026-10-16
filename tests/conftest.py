"""Shared pytest fixtures.

Unit tests never touch a database.
Integration tests use TEST_DATABASE_URL. If it is not set, they are skipped with a
clear message, so `pytest` still passes on a machine without MySQL running.

Each integration test runs inside a transaction that is rolled back at the end,
so tests never see each other's data and the test database stays clean.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from dotenv import load_dotenv
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app import create_app
from app.config import TestConfig
from app.db import SessionLocal, make_engine
from app.models import Base

load_dotenv()

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-mark everything under tests/integration and skip it when no test DB is set."""
    skip = pytest.mark.skip(reason="TEST_DATABASE_URL not set (see .env.example)")
    for item in items:
        if "integration" in str(item.path):
            item.add_marker(pytest.mark.integration)
            if not TEST_DATABASE_URL:
                item.add_marker(skip)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """Rebuild the test schema once per test run using the real Alembic migrations."""
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set")
    eng = make_engine(TEST_DATABASE_URL)
    with eng.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        Base.metadata.drop_all(conn)
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    os.environ["ALEMBIC_DATABASE_URL"] = TEST_DATABASE_URL
    command.upgrade(AlembicConfig("alembic.ini"), "head")
    yield eng
    eng.dispose()


@pytest.fixture
def app(engine: Engine) -> Iterator[Flask]:
    """A Flask app whose session is bound to a transaction we roll back afterwards."""
    connection = engine.connect()
    outer = connection.begin()

    flask_app = create_app(TestConfig, engine=engine)
    # Services call session.commit(); create_savepoint turns those into SAVEPOINTs
    # so the outer transaction can still be rolled back after the test.
    SessionLocal.configure(bind=connection, join_transaction_mode="create_savepoint")

    with flask_app.app_context():
        yield flask_app

    SessionLocal.remove()
    outer.rollback()
    connection.close()
    SessionLocal.configure(bind=engine, join_transaction_mode="conservative_savepoint")


@pytest.fixture
def db(app: Flask) -> Session:
    """The scoped session used by repositories during a test."""
    return SessionLocal()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
