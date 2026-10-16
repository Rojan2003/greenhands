from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TABLE_ARGS, Base
from app.models.enums import ActivityStatus

if TYPE_CHECKING:
    from app.models.location import Location
    from app.models.registration import Registration
    from app.models.user import User


class Activity(Base):
    """activities: a tree-planting event created by an admin at one location.

    Available slots are NOT stored here. They are computed as
    max_volunteers - count(registrations with status PENDING or APPROVED).
    """

    __tablename__ = "activities"
    __table_args__ = (
        # Database-level guards for the two rules in the brief.
        CheckConstraint("end_time > start_time", name="end_after_start"),
        CheckConstraint("max_volunteers > 0", name="max_volunteers_positive"),
        TABLE_ARGS,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    max_volunteers: Mapped[int] = mapped_column(Integer, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ActivityStatus] = mapped_column(
        Enum(ActivityStatus, name="activity_status", native_enum=True),
        nullable=False,
        default=ActivityStatus.OPEN,
        server_default=ActivityStatus.OPEN.value,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    creator: Mapped[User] = relationship(back_populates="created_activities")
    location: Mapped[Location] = relationship(back_populates="activities")
    registrations: Mapped[list[Registration]] = relationship(back_populates="activity")

    @property
    def starts_at(self) -> datetime:
        """Date + start time combined, used for the 'has not started' rule."""
        return datetime.combine(self.activity_date, self.start_time)

    def __repr__(self) -> str:
        return f"<Activity {self.id} {self.title}>"
