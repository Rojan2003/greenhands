# Progress

A feature is **done** only when it has validation, error handling, tests (one success +
one failure case), audit logging where needed, and a responsive UI.

## Where we are (updated 2026-10-17, afternoon)

| Phase | Status | Branch / PR |
|---|---|---|
| 0 Project setup | **Merged** | `feat/project-setup`, PR #1 |
| 1 Authentication | **Merged** + review hardening | `feat/auth` PR #2, `fix/auth-review` PR #3 |
| 2 Volunteer profile | **Merged** | `feat/profile`, PR #4 |
| 3 Admin: volunteers, locations, activities | **In progress** | `feat/admin-manage` (built in the main folder) |
| 4 Browse activities | **In progress** (parallel) | `feat/browse-activities` (built in the worktree `../greenhands-p4`) |
| 5-9 | Not started | one branch per phase, off `main` |

`main` is on GitHub (default branch) and only moves through pull requests. 218 unit +
integration tests and 3 Playwright tests pass on `main`; CI (ruff, mypy, pytest, e2e) is
green on every merged PR.

### How to resume work on this machine
1. Start MySQL from the terminal: `.\scripts\mysql.ps1` (XAMPP's own MariaDB; `stop` / `status` work too).
2. `git checkout main && git pull`, then `python scripts\upgrade_db.py` so an existing database gets new columns without losing data.
3. Run the app: `flask --app app run --debug` and open http://127.0.0.1:5000.
   Demo logins come from `python seed.py`: `admin` (SEED_ADMIN_PASSWORD in `.env`) and
   `maria`, `juan`, `liza`, `paolo` (SEED_VOLUNTEER_PASSWORD). Admins have no profile page by design.
4. Checks before any commit: `ruff format . && ruff check . && mypy . && pytest -q && pytest tests/e2e`.
   If the pages look unstyled, rebuild CSS with `.\scripts\tailwind.ps1` (app.css is git-ignored).
5. Never run two pytest suites against the same test database at once. For parallel work use a
   git worktree and set `TEST_DB_NAME` to another name in that worktree's `.env`.

### How each phase is built
Plan the phase in this file -> branch `feat/<name>` off `main` -> backend (schema, DAO, Pydantic
schema, service + unit tests) -> frontend (controller, templates, nav, integration + e2e tests, docs)
-> independent review (security, correctness, tests/docs) with every finding verified before it is
fixed -> merge `main` into the branch, full checks -> pull request -> CI green -> merge. Design
patterns to keep naming in code and in the defense: Singleton (`DatabaseManager`), MVC
(controllers / templates / models), inheritance (`Person` -> `Volunteer` / `Admin`), DAO (one class
per table, all SQL), Template Method (`BaseReport`).

### Next steps, in order
1. Finish Phase 3: merge `main` into `feat/admin-manage`, run all checks, open the PR, merge.
2. Finish Phase 4: merge `main` (brings Phase 3) into `feat/browse-activities`; expected overlaps are
   `app/navigation.py`, `app/__init__.py` (blueprint registration), `app/services/pagination.py` and
   `templates/partials/_pagination.html` (both phases add the same helper; keep one copy),
   `templates/volunteer/dashboard.html`, PROGRESS.md and REQUIREMENTS.md. Then checks, PR, merge.
3. Phase 5 (register for an activity) builds on Phase 4's details page: wire the Register button,
   `SELECT ... FOR UPDATE` on the activity inside one transaction, reuse a CANCELLED row, notify admins.
4. Then Phases 6, 7, 8, 9 as listed below, one branch and one PR each.

### Open items
- **Branch protection:** create the "Protect main" ruleset in GitHub (Settings -> Rules -> Rulesets):
  target the default branch; tick Restrict deletions, Block force pushes, Require a pull request
  (0 approvals), Require status checks with the check named `checks` and "up to date" on. Leave the rest off.
- `docs/design/erd.png` and `docs/design/reference.png` are still missing from the repo (needs the files from Rojan).
- Decided 2026-10-17: "Change Photo" shipped in Phase 2; "Forgot password?" is an admin "Reset password"
  action in Phase 3 (the brief has no email service), and the login page says "Ask an administrator".


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

## Phase 1: Authentication (merged: PR #2, hardening PR #3)
- [x] Pydantic schemas `SignUpSchema` / `LoginSchema` (`app/schemas/auth.py`) + `validate()` helper
- [x] `AuthService` (`app/services/auth_service.py`): sign-up creates user + profile + audit entry in one transaction; generic login error; 5 failures -> 15-minute lockout; counter reset on success; inactive accounts blocked
- [x] Role checks: `role_required` decorator + `require_role()` for services (`app/auth/roles.py`)
- [x] Login required app-wide except login, sign-up, health (`before_request` in `app/__init__.py`)
- [x] Rate limit on login (10/min) and sign-up (5/min)
- [x] Controllers: `auth` (login/logout/signup), `volunteer` dashboard, `admin` dashboard (+ `DashboardService`)
- [x] Templates: `base.html` header + sidebar (mobile toggle), split-screen login, sign-up, both dashboards, SVG placeholder images
- [x] Smoke test of login / logout / sign-up / dashboards / lockout with the test client (2026-10-17). Two fixes: password-mismatch error now shows on the confirm field even when other fields fail; the lockout message appears on the attempt that triggers the lock, not one attempt later
- [x] Tests: `tests/unit/test_schemas_auth.py`, `tests/unit/test_auth_service.py` (fake DAOs), `tests/unit/test_roles.py`, `tests/integration/test_auth_flow.py`, `tests/e2e/test_login.py` (Playwright, real server, CSRF on). 125 unit+integration and 2 e2e tests pass; CI runs the e2e step too
- [x] REQUIREMENTS.md rows FR-1, FR-2, FR-4, FR-6 and Usability updated
- [x] Independent code review (2026-10-17) and fixes: FR-8 error page no longer crashes for logged-in users when MySQL is down; failed-login counter is incremented under a row lock (`SELECT ... FOR UPDATE`) so parallel guesses cannot skip the lockout; deactivated accounts lose their session on the next request; passwords are limited to 72 *bytes*; `next=` redirect survives the login form and rejects `/\host`; rate limits now have tests (`tests/integration/test_auth_hardening.py`)

## Phase 2: Volunteer profile (merged: PR #4)
- [x] Schema: `users.photo_path` in `database/schema.sql`; `scripts/upgrade_db.py` adds missing columns to an existing database without wiping data (run it after pulling)
- [x] Pydantic schemas `ProfileSchema` / `ChangePasswordSchema` (`app/schemas/profile.py`): names 1-50, phone shape, address, birth date in the past and 13+, emergency contact; new password follows the sign-up rules and must differ from the current one
- [x] `ProfileService` (`app/services/profile_service.py`): every method VOLUNTEER-only (`require_role`); profile update upserts the `volunteer_profiles` row; password change verifies the current password; `check_photo()` accepts PNG/JPG/WEBP by extension AND magic bytes, max 2 MB
- [x] View / edit profile with validation (names, phone, address, birth date, emergency contact): `app/controllers/profile.py` (`/profile`, `/profile/edit`), `templates/volunteer/profile.html`, `profile_edit.html`
- [x] Change password (current password required): `/profile/password`, `templates/volunteer/change_password.html`; passwords are never echoed back
- [x] Change Photo: upload, type/size checks, default avatar fallback: inline form on the profile page posting to `/profile/photo`; files land in `instance/uploads/avatars/user_<id>.<ext>` (git-ignored, outside the public static folder) and are served to logged-in users only by `/profile/photo/<path>`; `partials/_avatar.html` shows the photo or initials in the header and on the profile page; oversized uploads get a friendly 413 page (`MAX_CONTENT_LENGTH` in `app/config.py`)
- [x] Audit log entries for profile and password changes: `PROFILE_UPDATED` (changed field names only, never values), `PASSWORD_CHANGED`, `PHOTO_UPDATED`
- [x] Navigation: "My Profile" sidebar link (`app/navigation.py`, highlighted on every `/profile` page), dashboard card "Edit Profile" opens the profile; login page says "Forgot your password? Ask an administrator."
- [x] Tests: `tests/unit/test_schemas_profile.py`, `tests/unit/test_profile_service.py` (fake DAOs, photo checks), `tests/unit/test_dao.py` (photo/password updates), `tests/integration/test_profile_flow.py` (view, 403 for admins, edit + audit, inline errors, password change + re-login, photo upload to a temp folder, bad file, 413), `tests/e2e/test_profile.py` (Playwright: edit phone from My Profile)
- [x] REQUIREMENTS.md rows FR-3, FR-4, FR-6 updated; README notes `scripts/upgrade_db.py` and the uploads folder
- [x] Review fixes: new passwords are limited to 72 *bytes* (shared `check_password_strength()` in `app/schemas/auth.py`, used by sign-up and change password); the avatar file is written inside the database transaction; photos moved out of `app/static` behind a login-protected route; integration test asserts the real birth-date error, not the form hint

## Phase 3: Admin activities and locations
- [ ] Users list for admins with "Reset password" and activate/deactivate (replaces "Forgot password?")
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
