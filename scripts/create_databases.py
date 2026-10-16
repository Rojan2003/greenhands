"""Create the `greenhands` and `greenhands_test` databases with utf8mb4.

Same effect as doing it by hand in phpMyAdmin. Safe to run more than once.
Usage:  python scripts/create_databases.py
"""

from __future__ import annotations

import os
import sys

import pymysql
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv()

DATABASES = ("greenhands", "greenhands_test")


def main() -> int:
    url = make_url(os.environ.get("DATABASE_URL", ""))
    conn = pymysql.connect(
        host=url.host or "127.0.0.1",
        port=url.port or 3306,
        user=url.username or "root",
        password=url.password or "",
    )
    try:
        with conn.cursor() as cur:
            for name in DATABASES:
                # Identifiers can't be bound parameters; the names are constants above.
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                print(f"database ready: {name}")
        conn.commit()
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
