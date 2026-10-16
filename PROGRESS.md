# Progress

A feature is **done** only when it has validation, error handling, tests (one success +
one failure case), audit logging where needed, and a responsive UI.

## Phase 0: Project setup
- [x] Repo structure (MVC: controllers / templates / models, plus services, dao, database)
- [x] `.gitignore`, `.gitattributes` (LF), `.env.example`, pinned `requirements.txt`, ruff + mypy strict
- [x] `database/schema.sql` (InnoDB, utf8mb4, ENUMs, CHECKs, indexes) + `scripts/init_db.py`
- [x] `DatabaseManager` singleton (reconnect, transactions, error translation for FR-8)
- [x] Domain models: `BaseEntity` -> abstract `Person.generate_report()` -> `Volunteer` / `Admin`
- [x] `BaseReport` template method (`fetch_data` -> `summarize` -> `format`)
- [x] DAO classes, one per table, all SQL with `%s` placeholders
- [x] Flask app factory, typed errors, JSON logging, friendly 503 page when MySQL is down
- [x] Seed script through the DAOs (`--big` adds 1,000 activities)
- [x] Tailwind v4 standalone build script with theme colours
- [x] Tests: models, singleton, template method, every DAO (happy + failure), integration (schema, FR-8 cases, round trips)
- [x] GitHub Actions CI (ruff, mypy, pytest on MySQL 8)
- [x] README, REQUIREMENTS.md (SRS mapping), PROGRESS.md
- [ ] `docs/design/erd.png` and `docs/design/reference.png` added to the repo (needs the files)

## Phase 1: Authentication (in progress, branch `feat/auth`)
- [x] Pydantic schemas `SignUpSchema` / `LoginSchema` (`app/schemas/auth.py`) + `validate()` helper
- [x] `AuthService` (`app/services/auth_service.py`): sign-up creates user + profile + audit entry in one transaction; generic login error; 5 failures -> 15-minute lockout; counter reset on success; inactive accounts blocked
- [x] Role checks: `role_required` decorator + `require_role()` for services (`app/auth/roles.py`)
- [x] Login required app-wide except login, sign-up, health (`before_request` in `app/__init__.py`)
- [x] Rate limit on login (10/min) and sign-up (5/min)
- [x] Controllers: `auth` (login/logout/signup), `volunteer` dashboard, `admin` dashboard (+ `DashboardService`)
- [x] Templates: `base.html` header + sidebar (mobile toggle), split-screen login, sign-up, both dashboards, SVG placeholder images
- [ ] **Not yet verified in a browser or test client** (smoke test was not run before stopping)
- [ ] Unit tests for `AuthService` and schemas (happy + failure), integration tests for sign-up / login / lockout, Playwright e2e login test (Chromium is installed)
- [ ] REQUIREMENTS.md rows FR-1, FR-2, FR-4 need the Phase 1 files and tests filled in

### Next session
1. Run a smoke test of login / logout / sign-up, fix anything that breaks.
2. Write the Phase 1 tests listed above, then update REQUIREMENTS.md.
3. Open the pull request for `feat/project-setup` once `main` exists (see open questions).

### Open questions
- **Remote `main` branch:** GitHub has no `main` yet (the repo was empty, so `feat/project-setup` became the default). Approve pushing the first scaffolding commit to `main` so pull requests can be opened.
- `docs/design/erd.png` and `docs/design/reference.png` are still missing from the repo.
- "Forgot password?" link and "Change Photo" button: build now or later? (needed before Phase 2)

## Phase 2: Volunteer profile
- [ ] View / edit profile with validation
- [ ] Decide: "Forgot password?" and "Change Photo" now or later

## Phase 3: Admin activities and locations
- [ ] Locations CRUD
- [ ] Activities CRUD; delete with registrations sets CANCELLED
- [ ] Audit log on every create / update / delete / cancel

## Phase 4: Browse activities
- [ ] OPEN activities list with search, filters (date, location, keyword) and pagination
- [ ] Details page with computed available slots

## Phase 5: Register for an activity
- [ ] Checks: OPEN, not already registered, slots available
- [ ] `SELECT ... FOR UPDATE` in one transaction; re-use cancelled row
- [ ] Notify admins

## Phase 6: Admin review
- [ ] Pending list; approve re-checks capacity; reject requires remarks
- [ ] reviewed_by / reviewed_at, notify volunteer, audit log

## Phase 7: My registrations, schedule, notifications
- [ ] Registration status list with tabs
- [ ] Cancel rules (PENDING/APPROVED and not started); notify admin + audit log
- [ ] Schedule + history; notifications with mark-as-read

## Phase 8: Reports and audit logs
- [ ] Reports on screen with filters; CSV export; printable view
- [ ] Audit log viewer with filters

## Phase 9: Polish and deploy
- [ ] Responsive + accessible UI, empty/error/loading states
- [ ] Demo seed data, README screenshots, 15-minute demo checklist, deployment guide
