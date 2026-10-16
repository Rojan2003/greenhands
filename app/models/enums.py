"""Enumerations stored as MySQL ENUM columns.

`StrEnum` means `UserStatus.ACTIVE == "ACTIVE"`, which keeps templates and
Pydantic schemas simple.
"""

from __future__ import annotations

from enum import StrEnum


class RoleName(StrEnum):
    VOLUNTEER = "VOLUNTEER"
    ADMIN = "ADMIN"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ActivityStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class RegistrationStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


# Registrations in these states take up a slot (brief: available = max - PENDING - APPROVED)
SLOT_TAKING_STATUSES: frozenset[RegistrationStatus] = frozenset(
    {RegistrationStatus.PENDING, RegistrationStatus.APPROVED}
)
