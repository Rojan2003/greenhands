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

## Phase 1: Authentication (branch `feat/auth`, ready for review)
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

### Next session
1. Approve pushing `main` (see open questions), then open pull requests for `feat/project-setup`, `feat/auth` and `feat/profile`.
2. Start Phase 3 (admin users list, locations, activities).

### Open questions
- **Remote `main` branch:** GitHub has no `main` yet (the repo was empty, so `feat/project-setup` became the default). Approve pushing the first scaffolding commit to `main` so pull requests can be opened.
- `docs/design/erd.png` and `docs/design/reference.png` are still missing from the repo.
- ~~"Forgot password?" link and "Change Photo" button~~ Decided 2026-10-17 (blanket approval from Rojan):
  "Change Photo" is built in Phase 2 as part of the profile page (upload, size/type validation, stored under `app/static/uploads/`).
  "Forgot password?" has no email service in the brief, so the login page will say "Forgot your password? Ask an administrator",
  and Phase 3 gives admins a "Reset password" action on the users list (temporary password, audit-logged).

## Phase 2: Volunteer profile (branch `feat/profile`, ready for review)
- [x] Schema: `users.photo_path` in `database/schema.sql`; `scripts/upgrade_db.py` adds missing columns to an existing database without wiping data (run it after pulling)
- [x] Pydantic schemas `ProfileSchema` / `ChangePasswordSchema` (`app/schemas/profile.py`): names 1-50, phone shape, address, birth date in the past and 13+, emergency contact; new password follows the sign-up rules and must differ from the current one
- [x] `ProfileService` (`app/services/profile_service.py`): every method VOLUNTEER-only (`require_role`); profile update upserts the `volunteer_profiles` row; password change verifies the current password; `check_photo()` accepts PNG/JPG/WEBP by extension AND magic bytes, max 2 MB
- [x] View / edit profile with validation (names, phone, address, birth date, emergency contact): `app/controllers/profile.py` (`/profile`, `/profile/edit`), `templates/volunteer/profile.html`, `profile_edit.html`
- [x] Change password (current password required): `/profile/password`, `templates/volunteer/change_password.html`; passwords are never echoed back
- [x] Change Photo: upload, type/size checks, default avatar fallback: inline form on the profile page posting to `/profile/photo`; files land in `app/static/uploads/avatars/user_<id>.<ext>` (git-ignored); `partials/_avatar.html` shows the photo or initials in the header and on the profile page; oversized uploads get a friendly 413 page (`MAX_CONTENT_LENGTH` in `app/config.py`)
- [x] Audit log entries for profile and password changes: `PROFILE_UPDATED` (changed field names only, never values), `PASSWORD_CHANGED`, `PHOTO_UPDATED`
- [x] Navigation: "My Profile" sidebar link (`app/navigation.py`, highlighted on every `/profile` page), dashboard card "Edit Profile" opens the profile; login page says "Forgot your password? Ask an administrator."
- [x] Tests: `tests/unit/test_schemas_profile.py`, `tests/unit/test_profile_service.py` (fake DAOs, photo checks), `tests/unit/test_dao.py` (photo/password updates), `tests/integration/test_profile_flow.py` (view, 403 for admins, edit + audit, inline errors, password change + re-login, photo upload to a temp folder, bad file, 413), `tests/e2e/test_profile.py` (Playwright: edit phone from My Profile)
- [x] REQUIREMENTS.md rows FR-3, FR-4, FR-6 updated; README notes `scripts/upgrade_db.py` and the uploads folder

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
