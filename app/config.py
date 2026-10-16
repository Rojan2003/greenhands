"""Application configuration loaded from environment variables.

`python-dotenv` reads the `.env` file (git-ignored) so secrets never live in code.
"""

from __future__ import annotations

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Default settings shared by every environment."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

    # Session cookie hardening (Section 6 of the brief)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # CSRF (Flask-WTF)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # token valid for the whole session

    # Rate limiting (Flask-Limiter). In-memory storage is fine for one process.
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True

    # Business rules
    LOGIN_MAX_FAILED_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 15
    BCRYPT_ROUNDS = 12


class TestConfig(Config):
    """Settings used by pytest. Tests pass their own database URL."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SECRET_KEY = "test-secret-key-not-for-production"
