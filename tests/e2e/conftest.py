"""Fixtures for the Playwright browser tests.

`live_server` starts the real Flask app (CSRF ON, like production) on a free
local port in a background thread, pointed at the test database, and seeds one
volunteer through AuthService so the browser can log in. The root conftest's
`clean_db` empties the tables afterwards.

Run with:  pytest tests/e2e      (needs `playwright install chromium` once)
"""

from __future__ import annotations

import socket
import threading
from collections.abc import Iterator

import pytest
from werkzeug.serving import make_server

from app import create_app
from app.config import TestConfig
from app.database import DatabaseManager
from app.services.auth_service import AuthService

E2E_USERNAME = "e2e_vol"
E2E_PASSWORD = "Browser123"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def live_server(clean_db: DatabaseManager) -> Iterator[str]:
    AuthService.build(clean_db).register_volunteer(
        {
            "username": E2E_USERNAME,
            "email": "e2e@example.com",
            "password": E2E_PASSWORD,
            "confirm_password": E2E_PASSWORD,
            "first_name": "Eve",
            "last_name": "Browser",
        }
    )
    clean_db.close()  # the server threads open their own connections

    app = create_app(TestConfig, overrides={"WTF_CSRF_ENABLED": True})
    port = _free_port()
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
