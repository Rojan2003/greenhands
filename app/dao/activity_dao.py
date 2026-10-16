"""ActivityDAO: SQL for the activities table.

Available slots are never stored. Every SELECT here computes `taken_slots`
with a correlated COUNT of PENDING + APPROVED registrations.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.dao.base_dao import BaseDAO
from app.models import Activity, ActivityStatus

# Shared SELECT so every method maps rows the same way.
_SELECT = """
SELECT a.id, a.created_by, a.location_id, a.title, a.description, a.activity_date,
       a.start_time, a.end_time, a.max_volunteers, a.requirements, a.status,
       a.created_at, a.updated_at,
       l.location_name,
       (SELECT COUNT(*) FROM registrations r
         WHERE r.activity_id = a.id AND r.status IN ('PENDING', 'APPROVED')) AS taken_slots
FROM activities a
JOIN locations l ON l.id = a.location_id
"""


class ActivityDAO(BaseDAO):
    def to_model(self, row: dict[str, Any]) -> Activity:
        return Activity(
            id=row["id"],
            created_by=row["created_by"],
            location_id=row["location_id"],
            title=row["title"],
            description=row["description"],
            activity_date=self.to_date(row["activity_date"]),
            start_time=self.to_time(row["start_time"]),
            end_time=self.to_time(row["end_time"]),
            max_volunteers=row["max_volunteers"],
            requirements=row["requirements"],
            status=ActivityStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            taken_slots=int(row.get("taken_slots") or 0),
            location_name=row.get("location_name"),
        )

    # ---- reads ----
    def find_by_id(self, activity_id: int) -> Activity | None:
        row = self.db.fetch_one(_SELECT + "WHERE a.id = %s", (activity_id,))
        return self.to_model(row) if row else None

    def find_by_title(self, title: str) -> Activity | None:
        row = self.db.fetch_one(_SELECT + "WHERE a.title = %s", (title,))
        return self.to_model(row) if row else None

    def lock_for_update(self, activity_id: int) -> Activity | None:
        """Row-lock the activity inside the caller's transaction (SELECT ... FOR UPDATE).

        Must be called inside `DatabaseManager().transaction()`; the lock is released
        when that transaction commits or rolls back.
        """
        row = self.db.fetch_one(_SELECT + "WHERE a.id = %s FOR UPDATE", (activity_id,))
        return self.to_model(row) if row else None

    def search(
        self,
        *,
        keyword: str | None = None,
        location_id: int | None = None,
        activity_date: date | None = None,
        status: ActivityStatus | None = ActivityStatus.OPEN,
        limit: int = 12,
        offset: int = 0,
    ) -> list[Activity]:
        """Filtered list for the browse page. Filters are optional; only set ones apply."""
        sql = _SELECT + "WHERE 1 = 1"
        params: list[Any] = []
        if status is not None:
            sql += " AND a.status = %s"
            params.append(status.value)
        if location_id is not None:
            sql += " AND a.location_id = %s"
            params.append(location_id)
        if activity_date is not None:
            sql += " AND a.activity_date = %s"
            params.append(activity_date)
        if keyword:
            sql += " AND (a.title LIKE %s OR a.description LIKE %s)"
            like = "%" + keyword + "%"  # the wildcard is part of the VALUE, not the SQL text
            params.extend([like, like])
        sql += " ORDER BY a.activity_date, a.start_time LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        return [self.to_model(r) for r in self.db.fetch_all(sql, tuple(params))]

    def count_search(
        self,
        *,
        keyword: str | None = None,
        location_id: int | None = None,
        activity_date: date | None = None,
        status: ActivityStatus | None = ActivityStatus.OPEN,
    ) -> int:
        sql = "SELECT COUNT(*) AS n FROM activities a WHERE 1 = 1"
        params: list[Any] = []
        if status is not None:
            sql += " AND a.status = %s"
            params.append(status.value)
        if location_id is not None:
            sql += " AND a.location_id = %s"
            params.append(location_id)
        if activity_date is not None:
            sql += " AND a.activity_date = %s"
            params.append(activity_date)
        if keyword:
            sql += " AND (a.title LIKE %s OR a.description LIKE %s)"
            like = "%" + keyword + "%"
            params.extend([like, like])
        row = self.db.fetch_one(sql, tuple(params))
        return int(row["n"]) if row else 0

    def list_all(self, *, limit: int = 50, offset: int = 0) -> list[Activity]:
        rows = self.db.fetch_all(
            _SELECT + "ORDER BY a.activity_date DESC, a.id DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        return [self.to_model(r) for r in rows]

    def count_all(self) -> int:
        row = self.db.fetch_one("SELECT COUNT(*) AS n FROM activities")
        return int(row["n"]) if row else 0

    def count_by_status(self) -> dict[str, int]:
        rows = self.db.fetch_all("SELECT status, COUNT(*) AS n FROM activities GROUP BY status")
        counts = {status.value: 0 for status in ActivityStatus}
        for r in rows:
            counts[r["status"]] = int(r["n"])
        return counts

    def registration_count(self, activity_id: int) -> int:
        row = self.db.fetch_one(
            "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = %s", (activity_id,)
        )
        return int(row["n"]) if row else 0

    # ---- writes ----
    def insert(self, activity: Activity) -> int:
        new_id = self.db.execute(
            "INSERT INTO activities (created_by, location_id, title, description, "
            "activity_date, start_time, end_time, max_volunteers, requirements, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                activity.created_by,
                activity.location_id,
                activity.title,
                activity.description,
                activity.activity_date,
                activity.start_time,
                activity.end_time,
                activity.max_volunteers,
                activity.requirements,
                activity.status.value,
            ),
        )
        activity.id = new_id
        return new_id

    def update(self, activity: Activity) -> bool:
        affected = self.db.execute(
            "UPDATE activities SET location_id = %s, title = %s, description = %s, "
            "activity_date = %s, start_time = %s, end_time = %s, max_volunteers = %s, "
            "requirements = %s, status = %s WHERE id = %s",
            (
                activity.location_id,
                activity.title,
                activity.description,
                activity.activity_date,
                activity.start_time,
                activity.end_time,
                activity.max_volunteers,
                activity.requirements,
                activity.status.value,
                activity.id,
            ),
        )
        return affected > 0

    def set_status(self, activity_id: int, status: ActivityStatus) -> bool:
        affected = self.db.execute(
            "UPDATE activities SET status = %s WHERE id = %s", (status.value, activity_id)
        )
        return affected > 0

    def delete(self, activity_id: int) -> bool:
        affected = self.db.execute("DELETE FROM activities WHERE id = %s", (activity_id,))
        return affected > 0
