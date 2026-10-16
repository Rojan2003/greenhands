"""Seed the database with demo data.

Usage:  python seed.py          (safe to run again: it skips rows that already exist)

Creates: 2 roles, 1 admin, 4 volunteers (with profiles), 3 locations, 6 activities.
Passwords come from .env (SEED_ADMIN_PASSWORD / SEED_VOLUNTEER_PASSWORD) and are
never written to the terminal.
"""

from __future__ import annotations

import os
import sys
from datetime import date, time, timedelta

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.db import make_engine
from app.models import (
    Activity,
    ActivityStatus,
    Location,
    Role,
    RoleName,
    User,
    VolunteerProfile,
)

load_dotenv()


def get_or_create_role(session: Session, name: RoleName) -> Role:
    role = session.scalar(select(Role).where(Role.name == name.value))
    if role is None:
        role = Role(name=name.value)
        session.add(role)
        session.flush()
    return role


def get_or_create_user(
    session: Session,
    *,
    role: Role,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    phone: str,
    password: str,
    with_profile: bool,
) -> User:
    user = session.scalar(select(User).where(User.username == username))
    if user is not None:
        return user
    user = User(
        role=role,
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        password_hash=hash_password(password),
    )
    if with_profile:
        user.profile = VolunteerProfile(
            address="123 Example Street, Green City",
            birth_date=date(2000, 1, 15),
            emergency_contact_name="Emergency Contact",
            emergency_contact_phone="0917-000-0000",
        )
    session.add(user)
    session.flush()
    return user


def get_or_create_location(session: Session, name: str, address: str, details: str) -> Location:
    loc = session.scalar(select(Location).where(Location.location_name == name))
    if loc is None:
        loc = Location(location_name=name, address=address, details=details)
        session.add(loc)
        session.flush()
    return loc


def seed(session: Session) -> None:
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD")
    volunteer_password = os.environ.get("SEED_VOLUNTEER_PASSWORD")
    if not admin_password or not volunteer_password:
        msg = "Set SEED_ADMIN_PASSWORD and SEED_VOLUNTEER_PASSWORD in .env first."
        raise RuntimeError(msg)

    admin_role = get_or_create_role(session, RoleName.ADMIN)
    volunteer_role = get_or_create_role(session, RoleName.VOLUNTEER)

    admin = get_or_create_user(
        session,
        role=admin_role,
        username="admin",
        email="admin@greenhands.local",
        first_name="Alex",
        last_name="Rivera",
        phone="0917-111-1111",
        password=admin_password,
        with_profile=False,
    )

    volunteers = [
        ("maria", "maria@example.com", "Maria", "Santos"),
        ("juan", "juan@example.com", "Juan", "Dela Cruz"),
        ("liza", "liza@example.com", "Liza", "Reyes"),
        ("paolo", "paolo@example.com", "Paolo", "Garcia"),
    ]
    for i, (username, email, first, last) in enumerate(volunteers, start=2):
        get_or_create_user(
            session,
            role=volunteer_role,
            username=username,
            email=email,
            first_name=first,
            last_name=last,
            phone=f"0917-{i:03d}-{i:04d}",
            password=volunteer_password,
            with_profile=True,
        )

    riverside = get_or_create_location(
        session,
        "Riverside Park",
        "Riverside Drive, Green City",
        "Meet at the main gate. Parking available.",
    )
    hillside = get_or_create_location(
        session,
        "Hillside Reserve",
        "Km 12, Mountain Road, Green City",
        "Steep trail, wear sturdy shoes.",
    )
    campus = get_or_create_location(
        session,
        "Community Campus Grounds",
        "University Avenue, Green City",
        "Flat ground, suitable for families.",
    )

    today = date.today()
    activities = [
        ("Riverbank Reforestation Drive", riverside, 7, 25, ActivityStatus.OPEN),
        ("Hillside Native Tree Planting", hillside, 14, 15, ActivityStatus.OPEN),
        ("Campus Green Corridor", campus, 21, 40, ActivityStatus.OPEN),
        ("Mangrove Seedling Day", riverside, 30, 20, ActivityStatus.OPEN),
        ("Trail Restoration Weekend", hillside, -10, 12, ActivityStatus.COMPLETED),
        ("Storm Recovery Replanting", campus, 3, 10, ActivityStatus.CLOSED),
    ]
    for title, location, days_from_now, max_vols, status in activities:
        exists = session.scalar(select(Activity).where(Activity.title == title))
        if exists is not None:
            continue
        session.add(
            Activity(
                creator=admin,
                location=location,
                title=title,
                description=(
                    f"Join us at {location.location_name} to plant native seedlings and "
                    "help restore green cover in our community."
                ),
                activity_date=today + timedelta(days=days_from_now),
                start_time=time(7, 0),
                end_time=time(11, 0),
                max_volunteers=max_vols,
                requirements="Bring water, wear closed shoes and a hat. Gloves provided.",
                status=status,
            )
        )
    session.flush()


def main() -> int:
    engine = make_engine(os.environ.get("DATABASE_URL", ""))
    with Session(engine) as session, session.begin():
        seed(session)
    print("Seed complete: roles, admin, 4 volunteers, 3 locations, 6 activities.")
    print("Login with username 'admin' or 'maria' and the passwords from your .env.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
