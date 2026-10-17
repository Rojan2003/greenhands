"""Unit tests for the DAO classes using FakeDatabaseManager (no MySQL).

Each DAO gets at least one happy-path and one failure-path test. The fake
records the SQL and parameters, so we can prove values go through %s
placeholders and never into the SQL text.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pytest

from app.dao import (
    ActivityDAO,
    AuditLogDAO,
    LocationDAO,
    NotificationDAO,
    RegistrationDAO,
    RoleDAO,
    UserDAO,
    VolunteerProfileDAO,
)
from app.errors import DatabaseError, NotFoundError
from app.models import (
    ActivityStatus,
    Admin,
    AuditLog,
    Location,
    Notification,
    Registration,
    RegistrationStatus,
    RoleName,
    Volunteer,
    VolunteerProfile,
)
from tests.conftest import FakeDatabaseManager

NOW = datetime(2030, 1, 1, 10, 0)


def user_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": 5,
        "role_id": 1,
        "role_name": "VOLUNTEER",
        "username": "maria",
        "email": "maria@example.com",
        "password_hash": "$2b$12$x",
        "first_name": "Maria",
        "last_name": "Santos",
        "phone": None,
        "status": "ACTIVE",
        "failed_login_attempts": 0,
        "locked_until": None,
        "created_at": NOW,
        "updated_at": NOW,
        "profile_id": 9,
        "address": "Street 1",
        "birth_date": date(2000, 1, 1),
        "emergency_contact_name": "Mom",
        "emergency_contact_phone": "123",
        "profile_created_at": NOW,
        "profile_updated_at": NOW,
    }
    row.update(overrides)
    return row


# ---- RoleDAO ----
def test_role_find_by_name_uses_placeholder(fake_db: FakeDatabaseManager) -> None:
    fake_db.rows = [{"id": 2, "name": "ADMIN"}]
    role = RoleDAO(fake_db).find_by_name(RoleName.ADMIN)  # type: ignore[arg-type]
    assert role.name == RoleName.ADMIN
    assert fake_db.last_params == ("ADMIN",)
    assert "ADMIN" not in fake_db.last_sql


def test_role_missing_raises_not_found(fake_db: FakeDatabaseManager) -> None:
    with pytest.raises(NotFoundError):
        RoleDAO(fake_db).find_by_name(RoleName.ADMIN)  # type: ignore[arg-type]


# ---- UserDAO ----
def test_user_dao_builds_volunteer_with_profile(fake_db: FakeDatabaseManager) -> None:
    fake_db.rows = [user_row()]
    person = UserDAO(fake_db).find_by_username("maria")  # type: ignore[arg-type]
    assert isinstance(person, Volunteer)
    assert person.profile is not None and person.profile.address == "Street 1"
    assert fake_db.last_params == ("maria",)


def test_user_dao_builds_admin_without_profile(fake_db: FakeDatabaseManager) -> None:
    fake_db.rows = [user_row(role_name="ADMIN", profile_id=None)]
    person = UserDAO(fake_db).find_by_id(5)  # type: ignore[arg-type]
    assert isinstance(person, Admin)


def test_user_dao_returns_none_when_missing(fake_db: FakeDatabaseManager) -> None:
    assert UserDAO(fake_db).find_by_email("nobody@x.y") is None  # type: ignore[arg-type]


def test_user_dao_insert_sets_id_and_binds_values(fake_db: FakeDatabaseManager) -> None:
    volunteer = Volunteer(
        role_id=1,
        role_name=RoleName.VOLUNTEER,
        username="new'; DROP TABLE users; --",
        email="n@x.y",
        password_hash="h",
        first_name="N",
        last_name="U",
    )
    new_id = UserDAO(fake_db).insert(volunteer)  # type: ignore[arg-type]
    assert new_id == 1 and volunteer.id == 1
    assert "DROP TABLE" not in fake_db.last_sql  # the injection text stayed a parameter
    assert fake_db.last_params[1] == "new'; DROP TABLE users; --"


def test_user_dao_propagates_database_error(fake_db: FakeDatabaseManager) -> None:
    fake_db.fail_with = DatabaseError()
    with pytest.raises(DatabaseError):
        UserDAO(fake_db).find_by_id(1)  # type: ignore[arg-type]


# ---- VolunteerProfileDAO ----
def test_profile_insert_and_update(fake_db: FakeDatabaseManager) -> None:
    dao = VolunteerProfileDAO(fake_db)  # type: ignore[arg-type]
    profile = VolunteerProfile(user_id=5, address="A")
    assert dao.insert(profile) == 1
    assert dao.update(profile) is True
    assert fake_db.last_params[-1] == 5  # WHERE user_id = %s


def test_profile_missing_returns_none(fake_db: FakeDatabaseManager) -> None:
    assert VolunteerProfileDAO(fake_db).find_by_user_id(99) is None  # type: ignore[arg-type]


# ---- LocationDAO ----
def test_location_round_trip(fake_db: FakeDatabaseManager) -> None:
    dao = LocationDAO(fake_db)  # type: ignore[arg-type]
    loc = Location(location_name="Park", address="Main")
    assert dao.insert(loc) == 1
    fake_db.rows = [{"id": 1, "location_name": "Park", "address": "Main", "details": None}]
    assert dao.find_by_id(1) == loc


def test_location_delete_returns_false_when_nothing_deleted(fake_db: FakeDatabaseManager) -> None:
    dao = LocationDAO(fake_db)  # type: ignore[arg-type]
    fake_db.execute = lambda sql, params=(): 0  # type: ignore[method-assign]
    assert dao.delete(42) is False


# ---- ActivityDAO ----
def activity_row() -> dict[str, Any]:
    return {
        "id": 3,
        "created_by": 1,
        "location_id": 2,
        "title": "Planting",
        "description": None,
        "activity_date": date(2030, 1, 1),
        "start_time": timedelta(hours=7),  # PyMySQL gives TIME as timedelta
        "end_time": timedelta(hours=11),
        "max_volunteers": 10,
        "requirements": None,
        "status": "OPEN",
        "created_at": NOW,
        "updated_at": NOW,
        "location_name": "Park",
        "taken_slots": 4,
    }


def test_activity_search_binds_keyword_with_like(fake_db: FakeDatabaseManager) -> None:
    fake_db.rows = [activity_row()]
    results = ActivityDAO(fake_db).search(keyword="plant", location_id=2)  # type: ignore[arg-type]
    assert results[0].available_slots == 6
    assert results[0].start_time.hour == 7
    assert "LIKE %s" in fake_db.last_sql
    assert fake_db.last_params == ("OPEN", 2, "%plant%", "%plant%", 12, 0)


def test_activity_lock_for_update_uses_for_update(fake_db: FakeDatabaseManager) -> None:
    fake_db.rows = [activity_row()]
    ActivityDAO(fake_db).lock_for_update(3)  # type: ignore[arg-type]
    assert fake_db.last_sql.endswith("FOR UPDATE")


def test_activity_missing_returns_none(fake_db: FakeDatabaseManager) -> None:
    assert ActivityDAO(fake_db).find_by_id(404) is None  # type: ignore[arg-type]


def test_activity_set_status(fake_db: FakeDatabaseManager) -> None:
    assert ActivityDAO(fake_db).set_status(3, ActivityStatus.CANCELLED)  # type: ignore[arg-type]
    assert fake_db.last_params == ("CANCELLED", 3)


# ---- RegistrationDAO ----
def test_registration_count_slot_taking(fake_db: FakeDatabaseManager) -> None:
    fake_db.rows = [{"n": 2}]
    assert RegistrationDAO(fake_db).count_slot_taking(3) == 2  # type: ignore[arg-type]
    assert "'PENDING', 'APPROVED'" in fake_db.last_sql


def test_registration_reopen_resets_review_fields(fake_db: FakeDatabaseManager) -> None:
    assert RegistrationDAO(fake_db).reopen(7)  # type: ignore[arg-type]
    assert "reviewed_by = NULL" in fake_db.last_sql
    assert fake_db.last_params == (7,)


def test_registration_review_binds_all_fields(fake_db: FakeDatabaseManager) -> None:
    RegistrationDAO(fake_db).review(  # type: ignore[arg-type]
        7, status=RegistrationStatus.REJECTED, reviewed_by=1, reviewed_at=NOW, remarks="Full"
    )
    assert fake_db.last_params == ("REJECTED", 1, NOW, "Full", 7)


def test_registration_missing_returns_none(fake_db: FakeDatabaseManager) -> None:
    assert RegistrationDAO(fake_db).find_by_activity_and_user(1, 1) is None  # type: ignore[arg-type]


def test_registration_insert_defaults_to_pending(fake_db: FakeDatabaseManager) -> None:
    reg = Registration(activity_id=3, user_id=5)
    RegistrationDAO(fake_db).insert(reg)  # type: ignore[arg-type]
    assert fake_db.last_params == (3, 5, "PENDING")


# ---- NotificationDAO ----
def test_notification_mark_read_is_scoped_to_user(fake_db: FakeDatabaseManager) -> None:
    NotificationDAO(fake_db).mark_read(10, 5)  # type: ignore[arg-type]
    assert "user_id = %s" in fake_db.last_sql
    assert fake_db.last_params == (10, 5)


def test_notification_insert_many_counts(fake_db: FakeDatabaseManager) -> None:
    n = NotificationDAO(fake_db).insert_many([1, 2, 3], "REGISTRATION", "New")  # type: ignore[arg-type]
    assert n == 3
    assert len(fake_db.calls) == 3


def test_notification_list_maps_is_read_to_bool(fake_db: FakeDatabaseManager) -> None:
    fake_db.rows = [
        {"id": 1, "user_id": 5, "type": "T", "message": "m", "is_read": 1, "created_at": NOW}
    ]
    items = NotificationDAO(fake_db).list_by_user(5)  # type: ignore[arg-type]
    assert items[0] == Notification(
        id=1, user_id=5, type="T", message="m", is_read=True, created_at=NOW
    )


# ---- AuditLogDAO ----
def test_audit_insert(fake_db: FakeDatabaseManager) -> None:
    entry = AuditLog(user_id=1, action="CREATE", entity="activity", record_reference=3)
    assert AuditLogDAO(fake_db).insert(entry) == 1  # type: ignore[arg-type]
    assert fake_db.last_params == (1, "CREATE", "activity", 3, None)


def test_audit_search_adds_only_given_filters(fake_db: FakeDatabaseManager) -> None:
    AuditLogDAO(fake_db).search(action="CREATE", date_from=date(2030, 1, 1))  # type: ignore[arg-type]
    assert "l.action = %s" in fake_db.last_sql
    assert "l.user_id = %s" not in fake_db.last_sql
    assert fake_db.last_params == ("CREATE", date(2030, 1, 1), 50, 0)
