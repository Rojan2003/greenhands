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
- [x] Independent code review (2026-10-17) and fixes: FR-8 error page no longer crashes for logged-in users when MySQL is down; failed-login counter is incremented under a row lock (`SELECT ... FOR UPDATE`) so parallel guesses cannot skip the lockout; deactivated accounts lose their session on the next request; passwords are limited to 72 *bytes*; `next=` redirect survives the login form and rejects `/\host`; rate limits now have tests (`tests/integration/test_auth_hardening.py`)

### Next session
1. Review and merge the `feat/admin-manage` pull request (Phase 3).
2. Start Phase 4 (browse activities for volunteers: reuse `Page` + `partials/_pagination.html` and `ActivityDAO.search()`).

### Open questions
- **Remote `main` branch:** GitHub has no `main` yet (the repo was empty, so `feat/project-setup` became the default). Approve pushing the first scaffolding commit to `main` so pull requests can be opened.
- `docs/design/erd.png` and `docs/design/reference.png` are still missing from the repo.
- ~~"Forgot password?" link and "Change Photo" button~~ Decided 2026-10-17 (blanket approval from Rojan):
  "Change Photo" is built in Phase 2 as part of the profile page (upload, size/type validation, stored under `instance/uploads/`).
  "Forgot password?" has no email service in the brief, so the login page will say "Forgot your password? Ask an administrator",
  and Phase 3 gives admins a "Reset password" action on the users list (temporary password, audit-logged).

## Phase 2: Volunteer profile (branch `feat/profile`, ready for review)
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

## Phase 3: Admin activities and locations (branch `feat/admin-manage`, ready for review)
- [x] Users list for admins with "Reset password" and activate/deactivate (replaces "Forgot password?"): `/admin/volunteers` (`app/controllers/admin_volunteers.py`, `templates/admin/volunteers.html`), 20 per page, search on name / username / email (`UserDAO.search_volunteers()` / `count_volunteers()`, LIKE wildcard in the value); `AdminUserService` (`app/services/admin_user_service.py`) lists volunteers only, refuses self-deactivation and admin targets, generates a 12-character temporary password with `secrets` (letter + digit guaranteed, no look-alike characters), stores only its hash, flashes it ONCE to the admin and notifies the volunteer
- [x] Locations CRUD: `/admin/locations` list with activity counts (`LocationDAO.list_with_activity_counts()`, LEFT JOIN + COUNT), new / edit (shared `templates/admin/locations/form.html`) and delete (`app/controllers/admin_locations.py`); `LocationSchema` (`app/schemas/location.py`); `LocationService` refuses duplicate names (inline field error) and deleting a location that still has activities
- [x] Activities CRUD; delete with registrations sets CANCELLED: `/admin/activities` list (10 per page, `?status=` filter, slots taken / max from `Activity.available_slots`), new / edit (shared `templates/admin/activities/form.html`, location drop-down), delete and status change (`app/controllers/admin_activities.py`); `ActivitySchema` (`app/schemas/activity.py`) parses the form text and refuses a past date only on create (validation context), end time must be after start; `ActivityService` keeps `max_volunteers` >= taken slots on edit, `delete_or_cancel()` deletes only when nobody ever registered, otherwise sets CANCELLED and notifies every PENDING / APPROVED registrant (`RegistrationDAO.list_user_ids_by_activity()`); `change_status()` to CANCELLED follows the same path
- [x] Audit log on every create / update / delete / cancel: `LOCATION_CREATED` / `_UPDATED` / `_DELETED`, `ACTIVITY_CREATED` / `_UPDATED` / `_DELETED` / `_CANCELLED` / `_STATUS_CHANGED` ("OPEN -> CLOSED"), `USER_ACTIVATED` / `USER_DEACTIVATED`, `PASSWORD_RESET` (details never contain the password), all written in the same transaction as the change
- [x] Shared pieces for later phases: `Page` dataclass (`app/services/pagination.py`) + `partials/_pagination.html` macro `paginate(page_obj, endpoint, **filters)`; `select_field` and `textarea_field` macros in `partials/_forms.html`; `status_badge` knows ACTIVE / INACTIVE
- [x] Navigation: sidebar "Manage Activities", "Manage Locations" and "Volunteers" open the new pages (highlighted on every page of their blueprint); the admin dashboard's "Total Activities" and "Total Volunteers" cards link to the lists ("Registrations", "Reports", "Audit Logs" stay at `#` until their phases)
- [x] Tests: `tests/unit/test_schemas_location_activity.py`, `test_location_service.py`, `test_activity_service.py`, `test_admin_user_service.py`, `test_pagination.py`, new DAO tests in `test_dao.py`; `tests/integration/test_admin_manage_flow.py` (403 for volunteers on every admin route, locations CRUD + duplicate name + delete refused, activities create / edit / filter / pagination / status change, delete-vs-cancel with notifications only for PENDING / APPROVED, volunteers search / pagination / deactivate blocks login / reset password then the temporary password logs in); `tests/e2e/test_admin_activities.py` (Playwright: admin creates a location and an activity through the forms, changes its status through the row form with `confirm()`). 371 unit+integration and 4 e2e tests pass
- [x] REQUIREMENTS.md rows FR-3, FR-4, FR-6 and Usability updated

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
