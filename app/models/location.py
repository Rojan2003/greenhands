from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TABLE_ARGS, Base

if TYPE_CHECKING:
    from app.models.activity import Activity


class Location(Base):
    """locations: a place that hosts zero or many activities."""

    __tablename__ = "locations"
    __table_args__ = (TABLE_ARGS,)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text)

    activities: Mapped[list[Activity]] = relationship(back_populates="location")

    def __repr__(self) -> str:
        return f"<Location {self.location_name}>"
