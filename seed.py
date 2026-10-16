"""Seed the database with demo data through the DAO layer.

Usage:
    python seed.py            # roles exist from schema.sql; adds 1 admin, 4 volunteers,
                              # 3 locations, 6 activities. Safe to run again (skips existing).
    python seed.py --big      # also adds 1,000 extra activities for the performance check
                              # (NFR: CRUD on 1,000 records within 2 seconds).

Passwords come from .env (SEED_ADMIN_PASSWORD / SEED_VOLUNTEER_PASSWORD) and are
never printed.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import date, time, timedelta
from typing import Any

from dotenv import load_dotenv

from app.auth.passwords import hash_password
from app.dao import ActivityDAO, LocationDAO, RoleDAO, UserDAO, VolunteerProfileDAO
from app.database import DatabaseManager
from app.models import (
    Activity,
    ActivityStatus,
    Admin,
    Location,
    Person,
    RoleName,
    Volunteer,
    VolunteerProfile,
)

load_dotenv()


class Seeder:
    """Small helper object so each step can share the DAOs."""

    def __init__(self) -> None:
        self.db = DatabaseManager()
        self.roles = RoleDAO(self.db)
        self.users = UserDAO(self.db)
        self.profiles = VolunteerProfileDAO(self.db)
        self.locations = LocationDAO(self.db)
        self.activities = ActivityDAO(self.db)

    # ---- users ----
    def ensure_user(
        self,
        *,
        role: RoleName,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        phone: str,
        password: str,
    ) -> Person:
        existing = self.users.find_by_username(username)
        if existing is not None:
            return existing
        role_row = self.roles.find_by_name(role)
        common: dict[str, Any] = {
            "role_id": role_row.id or 0,
            "role_name": role,
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
        }
        with self.db.transaction():  # user + profile succeed or fail together
            if role == RoleName.ADMIN:
                admin = Admin(**common)
                self.users.insert(admin)
                return admin
            volunteer = Volunteer(**common)
            self.users.insert(volunteer)
            profile = VolunteerProfile(
                user_id=volunteer.id or 0,
                address="123 Example Street, Green City",
                birth_date=date(2000, 1, 15),
                emergency_contact_name="Emergency Contact",
                emergency_contact_phone="0917-000-0000",
            )
            self.profiles.insert(profile)
            volunteer.profile = profile
            return volunteer

    # ---- locations ----
    def ensure_location(self, name: str, address: str, details: str) -> Location:
        existing = self.locations.find_by_name(name)
        if existing is not None:
            return existing
        location = Location(location_name=name, address=address, details=details)
        self.locations.insert(location)
        return location

    # ---- activities ----
    def ensure_activity(
        self,
        *,
        admin: Person,
        location: Location,
        title: str,
        days_from_now: int,
        max_volunteers: int,
        status: ActivityStatus,
    ) -> Activity:
        existing = self.activities.find_by_title(title)
        if existing is not None:
            return existing
        activity = Activity(
            created_by=admin.id or 0,
            location_id=location.id or 0,
            title=title,
            description=(
                f"Join us at {location.location_name} to plant native seedlings and "
                "help restore green cover in our community."
            ),
            activity_date=date.today() + timedelta(days=days_from_now),
            start_time=time(7, 0),
            end_time=time(11, 0),
            max_volunteers=max_volunteers,
            requirements="Bring water, wear closed shoes and a hat. Gloves provided.",
            status=status,
        )
        activity.validate()
        self.activities.insert(activity)
        return activity

    def seed_big(self, admin: Person, locations: list[Location], count: int = 1000) -> int:
        """Bulk activities for the performance requirement. Inserted in one transaction."""
        rng = random.Random(42)  # fixed seed = same demo data every time
        created = 0
        with self.db.transaction():
            for n in range(1, count + 1):
                title = f"Bulk Planting Session #{n:04d}"
                if self.activities.find_by_title(title) is not None:
                    continue
                location = rng.choice(locations)
                start_hour = rng.choice([6, 7, 8, 13, 14])
                self.activities.insert(
                    Activity(
                        created_by=admin.id or 0,
                        location_id=location.id or 0,
                        title=title,
                        description=f"Generated demo activity {n} at {location.location_name}.",
                        activity_date=date.today() + timedelta(days=rng.randint(-120, 180)),
                        start_time=time(start_hour, 0),
                        end_time=time(start_hour + 3, 0),
                        max_volunteers=rng.randint(5, 40),
                        requirements="Standard field kit.",
                        status=rng.choice(list(ActivityStatus)),
                    )
                )
                created += 1
        return created


def run(big: bool = False) -> None:
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD")
    volunteer_password = os.environ.get("SEED_VOLUNTEER_PASSWORD")
    if not admin_password or not volunteer_password:
        msg = "Set SEED_ADMIN_PASSWORD and SEED_VOLUNTEER_PASSWORD in .env first."
        raise RuntimeError(msg)

    seeder = Seeder()
    admin = seeder.ensure_user(
        role=RoleName.ADMIN,
        username="admin",
        email="admin@greenhands.local",
        first_name="Alex",
        last_name="Rivera",
        phone="0917-111-1111",
        password=admin_password,
    )
    volunteers = [
        ("maria", "maria@example.com", "Maria", "Santos"),
        ("juan", "juan@example.com", "Juan", "Dela Cruz"),
        ("liza", "liza@example.com", "Liza", "Reyes"),
        ("paolo", "paolo@example.com", "Paolo", "Garcia"),
    ]
    for i, (username, email, first, last) in enumerate(volunteers, start=2):
        seeder.ensure_user(
            role=RoleName.VOLUNTEER,
            username=username,
            email=email,
            first_name=first,
            last_name=last,
            phone=f"0917-{i:03d}-{i:04d}",
            password=volunteer_password,
        )

    riverside = seeder.ensure_location(
        "Riverside Park", "Riverside Drive, Green City", "Meet at the main gate. Parking available."
    )
    hillside = seeder.ensure_location(
        "Hillside Reserve", "Km 12, Mountain Road, Green City", "Steep trail, wear sturdy shoes."
    )
    campus = seeder.ensure_location(
        "Community Campus Grounds", "University Avenue, Green City", "Flat ground, family friendly."
    )

    plan = [
        ("Riverbank Reforestation Drive", riverside, 7, 25, ActivityStatus.OPEN),
        ("Hillside Native Tree Planting", hillside, 14, 15, ActivityStatus.OPEN),
        ("Campus Green Corridor", campus, 21, 40, ActivityStatus.OPEN),
        ("Mangrove Seedling Day", riverside, 30, 20, ActivityStatus.OPEN),
        ("Trail Restoration Weekend", hillside, -10, 12, ActivityStatus.COMPLETED),
        ("Storm Recovery Replanting", campus, 3, 10, ActivityStatus.CLOSED),
    ]
    for title, location, days, max_vols, status in plan:
        seeder.ensure_activity(
            admin=admin,
            location=location,
            title=title,
            days_from_now=days,
            max_volunteers=max_vols,
            status=status,
        )

    print("Seed complete: admin, 4 volunteers, 3 locations, 6 activities.")
    if big:
        created = seeder.seed_big(admin, [riverside, hillside, campus])
        print(f"Big seed: {created} extra activities inserted.")
    print("Log in as 'admin' or 'maria' with the passwords from your .env.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed demo data.")
    parser.add_argument("--big", action="store_true", help="add 1,000 extra activities")
    args = parser.parse_args()
    run(big=args.big)
    return 0


if __name__ == "__main__":
    sys.exit(main())
