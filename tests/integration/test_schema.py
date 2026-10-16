"""Integration tests: the migration really creates the schema on MySQL/MariaDB."""

from __future__ import annotations

from datetime import date, time

import pytest
from flask.testing import FlaskClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.models import Activity, Location, Registration, Role, User


def _make_admin(db: Session) -> User:
    role = Role(name="ADMIN")
    user = User(
        role=role,
        username="admin_t",
        email="admin_t@example.com",
        password_hash="x",
        first_name="A",
        last_name="D",
    )
    db.add(user)
    db.flush()
    return user


def test_migration_created_all_tables_with_innodb_utf8mb4(db: Session) -> None:
    rows = db.execute(
        text(
            "SELECT table_name, engine, table_collation FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name <> 'alembic_version'"
        )
    ).all()
    names = {r[0] for r in rows}
    assert names == {
        "roles",
        "users",
        "volunteer_profiles",
        "locations",
        "activities",
        "registrations",
        "notifications",
        "audit_logs",
    }
    for _name, engine, collation in rows:
        assert engine == "InnoDB"
        assert collation.startswith("utf8mb4")


def test_duplicate_registration_is_rejected_by_database(db: Session) -> None:
    admin = _make_admin(db)
    loc = Location(location_name="L", address="A")
    act = Activity(
        creator=admin,
        location=loc,
        title="T",
        activity_date=date(2030, 1, 1),
        start_time=time(8, 0),
        end_time=time(10, 0),
        max_volunteers=5,
    )
    db.add(act)
    db.flush()
    db.add(Registration(activity=act, user=admin))
    db.flush()
    db.add(Registration(activity=act, user=admin))
    with pytest.raises(IntegrityError):
        db.flush()


def test_check_constraint_rejects_zero_capacity(db: Session) -> None:
    admin = _make_admin(db)
    db.add(
        Activity(
            creator=admin,
            location=Location(location_name="L", address="A"),
            title="Bad",
            activity_date=date(2030, 1, 1),
            start_time=time(8, 0),
            end_time=time(10, 0),
            max_volunteers=0,
        )
    )
    with pytest.raises((IntegrityError, OperationalError)):
        db.flush()


def test_health_endpoint_reaches_database(client: FlaskClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
