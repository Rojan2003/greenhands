"""UserDAO: SQL for the users table (joined with roles and volunteer_profiles).

Returns Volunteer or Admin objects depending on the role (polymorphism):
the rest of the app never has to look at role_id to know what kind of Person it has.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.dao.base_dao import BaseDAO
from app.models import Admin, Person, RoleName, UserStatus, Volunteer, VolunteerProfile

# One SELECT used by every "find" so the mapping is always the same.
_SELECT = """
SELECT u.id, u.role_id, u.username, u.email, u.password_hash, u.first_name, u.last_name,
       u.phone, u.status, u.failed_login_attempts, u.locked_until, u.created_at, u.updated_at,
       r.name AS role_name,
       p.id AS profile_id, p.address, p.birth_date, p.emergency_contact_name,
       p.emergency_contact_phone, p.created_at AS profile_created_at,
       p.updated_at AS profile_updated_at
FROM users u
JOIN roles r ON r.id = u.role_id
LEFT JOIN volunteer_profiles p ON p.user_id = u.id
"""


class UserDAO(BaseDAO):
    @staticmethod
    def to_model(row: dict[str, Any]) -> Person:
        """Build an Admin or a Volunteer (with profile, when one exists) from a joined row."""
        common: dict[str, Any] = {
            "id": row["id"],
            "role_id": row["role_id"],
            "role_name": RoleName(row["role_name"]),
            "username": row["username"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "phone": row["phone"],
            "status": UserStatus(row["status"]),
            "failed_login_attempts": row["failed_login_attempts"],
            "locked_until": row["locked_until"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        if common["role_name"] == RoleName.ADMIN:
            return Admin(**common)
        profile = None
        if row.get("profile_id") is not None:
            profile = VolunteerProfile(
                id=row["profile_id"],
                user_id=row["id"],
                address=row["address"],
                birth_date=row["birth_date"],
                emergency_contact_name=row["emergency_contact_name"],
                emergency_contact_phone=row["emergency_contact_phone"],
                created_at=row["profile_created_at"],
                updated_at=row["profile_updated_at"],
            )
        return Volunteer(**common, profile=profile)

    # ---- reads ----
    def find_by_id(self, user_id: int) -> Person | None:
        row = self.db.fetch_one(_SELECT + "WHERE u.id = %s", (user_id,))
        return self.to_model(row) if row else None

    def find_by_username(self, username: str) -> Person | None:
        row = self.db.fetch_one(_SELECT + "WHERE u.username = %s", (username,))
        return self.to_model(row) if row else None

    def find_by_email(self, email: str) -> Person | None:
        row = self.db.fetch_one(_SELECT + "WHERE u.email = %s", (email,))
        return self.to_model(row) if row else None

    def username_exists(self, username: str) -> bool:
        row = self.db.fetch_one("SELECT 1 AS found FROM users WHERE username = %s", (username,))
        return row is not None

    def email_exists(self, email: str) -> bool:
        row = self.db.fetch_one("SELECT 1 AS found FROM users WHERE email = %s", (email,))
        return row is not None

    def count_by_role(self, role: RoleName) -> int:
        row = self.db.fetch_one(
            "SELECT COUNT(*) AS n FROM users u JOIN roles r ON r.id = u.role_id WHERE r.name = %s",
            (role.value,),
        )
        return int(row["n"]) if row else 0

    def list_by_role(self, role: RoleName, *, limit: int = 50, offset: int = 0) -> list[Person]:
        rows = self.db.fetch_all(
            _SELECT + "WHERE r.name = %s ORDER BY u.last_name, u.first_name LIMIT %s OFFSET %s",
            (role.value, limit, offset),
        )
        return [self.to_model(r) for r in rows]

    def list_admin_ids(self) -> list[int]:
        rows = self.db.fetch_all(
            "SELECT u.id FROM users u JOIN roles r ON r.id = u.role_id WHERE r.name = %s",
            (RoleName.ADMIN.value,),
        )
        return [int(r["id"]) for r in rows]

    # ---- writes ----
    def insert(self, person: Person) -> int:
        """Insert the users row and return the new id (profiles: VolunteerProfileDAO)."""
        new_id = self.db.execute(
            "INSERT INTO users (role_id, username, email, password_hash, first_name, last_name, "
            "phone, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                person.role_id,
                person.username,
                person.email,
                person.password_hash,
                person.first_name,
                person.last_name,
                person.phone,
                person.status.value,
            ),
        )
        person.id = new_id
        return new_id

    def update_contact(
        self, user_id: int, *, first_name: str, last_name: str, phone: str | None
    ) -> bool:
        affected = self.db.execute(
            "UPDATE users SET first_name = %s, last_name = %s, phone = %s WHERE id = %s",
            (first_name, last_name, phone, user_id),
        )
        return affected > 0

    def record_failed_login(
        self, user_id: int, attempts: int, locked_until: datetime | None
    ) -> None:
        self.db.execute(
            "UPDATE users SET failed_login_attempts = %s, locked_until = %s WHERE id = %s",
            (attempts, locked_until, user_id),
        )

    def reset_failed_logins(self, user_id: int) -> None:
        self.db.execute(
            "UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = %s",
            (user_id,),
        )

    def set_status(self, user_id: int, status: UserStatus) -> bool:
        affected = self.db.execute(
            "UPDATE users SET status = %s WHERE id = %s", (status.value, user_id)
        )
        return affected > 0
