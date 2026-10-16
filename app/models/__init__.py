"""Import every model here so `Base.metadata` knows all tables (needed by Alembic)."""

from app.models.activity import Activity
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.enums import (
    SLOT_TAKING_STATUSES,
    ActivityStatus,
    RegistrationStatus,
    RoleName,
    UserStatus,
)
from app.models.location import Location
from app.models.notification import Notification
from app.models.registration import Registration
from app.models.role import Role
from app.models.user import User
from app.models.volunteer_profile import VolunteerProfile

__all__ = [
    "SLOT_TAKING_STATUSES",
    "Activity",
    "ActivityStatus",
    "AuditLog",
    "Base",
    "Location",
    "Notification",
    "Registration",
    "RegistrationStatus",
    "Role",
    "RoleName",
    "User",
    "UserStatus",
    "VolunteerProfile",
]
