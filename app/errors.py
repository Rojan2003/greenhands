"""Typed errors raised by the service layer.

Blueprints catch these and turn them into flash messages or HTTP status codes.
Services never return HTTP responses themselves.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application errors."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    """Input failed validation (bad types, lengths, missing fields, rule violations)."""

    status_code = 422

    def __init__(self, message: str, errors: dict[str, str] | None = None) -> None:
        super().__init__(message)
        # field name -> human readable message, so forms can show errors inline
        self.errors: dict[str, str] = errors or {}


class NotFoundError(AppError):
    """The requested record does not exist."""

    status_code = 404


class ConflictError(AppError):
    """The action clashes with current state (duplicate, full activity, already registered...)."""

    status_code = 409


class ForbiddenError(AppError):
    """The user is authenticated but not allowed to do this."""

    status_code = 403
