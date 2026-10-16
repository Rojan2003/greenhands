from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TABLE_ARGS, Base

if TYPE_CHECKING:
    from app.models.user import User


class Role(Base):
    """roles: VOLUNTEER or ADMIN. One role is assigned to many users."""

    __tablename__ = "roles"
    __table_args__ = (TABLE_ARGS,)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="role")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
