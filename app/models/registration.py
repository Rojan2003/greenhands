from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.models.base_entity import BaseEntity
from app.models.enums import SLOT_TAKING_STATUSES, RegistrationStatus


@dataclass(kw_only=True)
class Registration(BaseEntity):
    """registrations table: one volunteer signed up for one activity.

    UNIQUE(activity_id, user_id): a volunteer has at most one row per activity.
    Cancel + register again re-uses the row (status goes back to PENDING).
    """

    activity_id: int
    user_id: int
    status: RegistrationStatus = RegistrationStatus.PENDING
    registration_date: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by: int | None = None
    remarks: str | None = None

    # Filled by joins for list pages (not stored here)
    activity_title: str | None = field(default=None, compare=False)
    activity_date: date | None = field(default=None, compare=False)
    volunteer_name: str | None = field(default=None, compare=False)

    @property
    def takes_slot(self) -> bool:
        return self.status in SLOT_TAKING_STATUSES

    @property
    def can_be_cancelled(self) -> bool:
        return self.status in SLOT_TAKING_STATUSES
