"""NotificationService: in-app messages. Phase 1 only needs the unread badge count."""

from __future__ import annotations

from dataclasses import dataclass

from app.dao import NotificationDAO
from app.database import DatabaseManager
from app.models import Notification


@dataclass
class NotificationService:
    notifications: NotificationDAO

    @classmethod
    def build(cls, db: DatabaseManager | None = None) -> NotificationService:
        return cls(notifications=NotificationDAO(db or DatabaseManager()))

    def unread_count(self, user_id: int) -> int:
        return self.notifications.unread_count(user_id)

    def list_for_user(self, user_id: int) -> list[Notification]:
        return self.notifications.list_by_user(user_id)
