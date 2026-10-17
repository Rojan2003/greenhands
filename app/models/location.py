from __future__ import annotations

from dataclasses import dataclass

from app.models.base_entity import BaseEntity


@dataclass(kw_only=True)
class Location(BaseEntity):
    """locations table: a place that hosts zero or many activities."""

    location_name: str
    address: str
    details: str | None = None
