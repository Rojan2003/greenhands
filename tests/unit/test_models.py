"""Unit tests for the data model. No database needed: we inspect the metadata."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, UniqueConstraint

from app.models import (
    SLOT_TAKING_STATUSES,
    ActivityStatus,
    Base,
    RegistrationStatus,
    User,
    UserStatus,
)

EXPECTED_TABLES = {
    "roles",
    "users",
    "volunteer_profiles",
    "locations",
    "activities",
    "registrations",
    "notifications",
    "audit_logs",
}


def test_all_eight_tables_are_defined() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_every_table_uses_innodb_and_utf8mb4() -> None:
    for table in Base.metadata.tables.values():
        assert table.kwargs.get("mysql_engine") == "InnoDB", table.name
        assert table.kwargs.get("mysql_charset") == "utf8mb4", table.name


def test_registration_is_unique_per_user_and_activity() -> None:
    uniques = [
        c
        for c in Base.metadata.tables["registrations"].constraints
        if isinstance(c, UniqueConstraint)
    ]
    columns = {tuple(col.name for col in c.columns) for c in uniques}
    assert ("activity_id", "user_id") in columns


def test_activity_has_business_rule_check_constraints() -> None:
    checks = {
        str(c.sqltext)
        for c in Base.metadata.tables["activities"].constraints
        if isinstance(c, CheckConstraint)
    }
    assert "end_time > start_time" in checks
    assert "max_volunteers > 0" in checks


def test_enum_values_match_the_brief() -> None:
    assert [s.value for s in UserStatus] == ["ACTIVE", "INACTIVE"]
    assert [s.value for s in ActivityStatus] == ["OPEN", "CLOSED", "CANCELLED", "COMPLETED"]
    assert [s.value for s in RegistrationStatus] == [
        "PENDING",
        "APPROVED",
        "REJECTED",
        "CANCELLED",
        "COMPLETED",
    ]


def test_only_pending_and_approved_take_slots() -> None:
    assert {RegistrationStatus.PENDING, RegistrationStatus.APPROVED} == SLOT_TAKING_STATUSES


def test_user_name_helpers() -> None:
    user = User(first_name="Maria", last_name="Santos")
    assert user.full_name == "Maria Santos"
    assert user.initials == "MS"


def test_user_initials_handles_missing_last_name() -> None:
    user = User(first_name="Cher", last_name="")
    assert user.initials == "C"
