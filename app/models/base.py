"""Declarative base shared by every model.

- `TABLE_ARGS` forces InnoDB + utf8mb4 on every table (brief, Section 3).
- The naming convention gives every index/constraint a predictable name, which
  Alembic needs to be able to drop or alter them later.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

TABLE_ARGS: dict[str, Any] = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
