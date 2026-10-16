from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TABLE_ARGS, Base
from app.models.enums import UserStatus

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.audit_log import AuditLog
    from app.models.notification import Notification
    from app.models.registration import Registration
    from app.models.role import Role
    from app.models.volunteer_profile import VolunteerProfile


class User(Base):
    """users: login account for both volunteers and admins."""

    __tablename__ = "users"
    __table_args__ = (TABLE_ARGS,)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=True),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # --- relationships (names match the ERD verbs) ---
    role: Mapped[Role] = relationship(back_populates="users")
    profile: Mapped[VolunteerProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    registrations: Mapped[list[Registration]] = relationship(
        back_populates="user", foreign_keys="Registration.user_id"
    )
    reviewed_registrations: Mapped[list[Registration]] = relationship(
        back_populates="reviewer", foreign_keys="Registration.reviewed_by"
    )
    created_activities: Mapped[list[Activity]] = relationship(back_populates="creator")
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="user")

    # --- helpers ---
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def initials(self) -> str:
        return f"{self.first_name[:1]}{self.last_name[:1]}".upper()

    def __repr__(self) -> str:
        return f"<User {self.username}>"
