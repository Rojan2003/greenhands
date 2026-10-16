from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TABLE_ARGS, Base
from app.models.enums import RegistrationStatus

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.user import User


class Registration(Base):
    """registrations: one volunteer signing up for one activity.

    UNIQUE(activity_id, user_id) means a volunteer has at most one row per activity.
    If they cancel and register again, the same row is set back to PENDING.
    """

    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint("activity_id", "user_id", name="uq_registrations_activity_user"),
        TABLE_ARGS,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus, name="registration_status", native_enum=True),
        nullable=False,
        default=RegistrationStatus.PENDING,
        server_default=RegistrationStatus.PENDING.value,
        index=True,
    )
    registration_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    remarks: Mapped[str | None] = mapped_column(Text)

    activity: Mapped[Activity] = relationship(back_populates="registrations")
    user: Mapped[User] = relationship(back_populates="registrations", foreign_keys=[user_id])
    reviewer: Mapped[User | None] = relationship(
        back_populates="reviewed_registrations", foreign_keys=[reviewed_by]
    )

    def __repr__(self) -> str:
        return f"<Registration {self.id} user={self.user_id} activity={self.activity_id}>"
