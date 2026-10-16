# GreenHands

A tree-planting **volunteer registration and scheduling** web app.
Volunteers sign up, browse activities and register. Admins manage activities,
review registrations, and view reports and audit logs.

Built with **Python 3.12 / Flask / SQLAlchemy 2 / MySQL (MariaDB via XAMPP) / Tailwind CSS**.

> Status: Phase 0 (project setup) complete. See [PROGRESS.md](PROGRESS.md).

## Requirements

- Windows 11 with [XAMPP](https://www.apachefriends.org/) (MariaDB 10.4 or newer)
- Python 3.12 (`py -3.12 --version`)
- Git, and the [GitHub CLI](https://cli.github.com/) if you want to open pull requests

## Setup (Windows / PowerShell)

```powershell
# 1. Clone and enter the project
git clone https://github.com/Rojan2003/greenhands.git
cd greenhands

# 2. Create and activate a virtual environment
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies (runtime + dev tools)
pip install -r requirements-dev.txt

# 4. Create your .env from the example, then set SECRET_KEY to a long random value
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # paste the output into .env

# 5. Start MySQL: open the XAMPP Control Panel and click "Start" next to MySQL
#    (or run C:\xampp\mysql_start.bat)

# 6. Create the two databases (same as creating them in phpMyAdmin with utf8mb4_unicode_ci)
python scripts\create_databases.py

# 7. Create the tables
alembic upgrade head

# 8. Load demo data (passwords come from SEED_* values in .env)
python seed.py

# 9. Build the CSS (downloads the Tailwind standalone CLI once, no Node needed)
.\scripts\tailwind.ps1

# 10. Run the dev server
flask --app app run --debug
```

Open <http://127.0.0.1:5000>. Demo logins (after seeding): `admin` and `maria`,
with the passwords you put in `.env`.

## Commands

| Task | Command |
|---|---|
| Activate venv | `.\venv\Scripts\Activate.ps1` |
| Start MySQL | XAMPP Control Panel -> MySQL -> Start |
| Run migrations | `alembic upgrade head` |
| New migration after a model change | `alembic revision --autogenerate -m "describe change"` |
| Seed demo data | `python seed.py` |
| Dev server | `flask --app app run --debug` |
| Unit + integration tests | `pytest` |
| End-to-end tests (Phase 1+) | `playwright install chromium` once, then `pytest tests/e2e` |
| Lint | `ruff check .` |
| Format check / fix | `ruff format --check .` / `ruff format .` |
| Type check | `mypy .` |
| Everything CI runs | `.\scripts\check.ps1` |
| Build Tailwind CSS | `.\scripts\tailwind.ps1` (add `-Watch` while editing templates) |

## Project layout

```
app/
  __init__.py        Flask app factory (create_app)
  config.py          settings loaded from .env
  db.py              SQLAlchemy engine + per-request session
  errors.py          ValidationError, NotFoundError, ConflictError, ForbiddenError
  extensions.py      Flask-Login, CSRF, rate limiter
  logging_config.py  JSON logger
  auth/              user loader, password hashing, role decorators
  blueprints/        routes only (no database code here)
  services/          business rules
  repositories/      all database access, one per main table
  models/            SQLAlchemy ORM models (8 tables)
  schemas/           Pydantic validation
  templates/         Jinja2 HTML
  static/src/        Tailwind input (theme colours live here)
migrations/          Alembic migrations
scripts/             helper scripts (databases, Tailwind, checks)
tests/unit           no database
tests/integration    real MySQL/MariaDB test database (TEST_DATABASE_URL)
tests/e2e            Playwright browser tests
docs/design/         erd.png and reference.png (design references)
```

Request flow: **blueprint -> service -> repository -> database**. Templates and routes
never touch SQLAlchemy sessions directly.

## Database notes

- All tables use **InnoDB** and **utf8mb4** (set in `app/models/base.py`).
- Available slots are **computed** (`max_volunteers - PENDING - APPROVED`), never stored.
- Two `CHECK` constraints guard `end_time > start_time` and `max_volunteers > 0`.
  MariaDB 10.2+ and MySQL 8.0.16+ enforce them.
- XAMPP ships **MariaDB 10.4**. CI runs the same tests on **MySQL 8**, so both are covered.

## Tests

- `tests/unit` runs with no database.
- `tests/integration` needs `TEST_DATABASE_URL` in `.env` (a separate `greenhands_test`
  database). Each test runs inside a transaction that is rolled back, so the test
  database stays clean. If the variable is missing the tests are skipped, not failed.

## Line endings

`.gitattributes` forces LF for all text files. On Windows this works fine with the
default `core.autocrlf=true`; Git converts on checkout and commit.

## Image credits

Placeholder images will be added in Phase 4 (free images from Unsplash, credited here).
