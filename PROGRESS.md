# Progress

A feature is **done** only when it has validation, error handling, tests (one success +
one failure case), audit logging where needed, and a responsive UI.

## Phase 0: Project setup
- [x] Repo structure, `.gitignore`, `.gitattributes` (LF), `.env.example`
- [x] Pinned dependencies (`requirements.txt`, `requirements-dev.txt`), ruff + mypy strict config
- [x] Flask app factory, config, typed errors, JSON logging, DB session
- [x] 8 SQLAlchemy models (InnoDB, utf8mb4, enums, check constraints)
- [x] Alembic set up + initial migration (verified on MariaDB 10.4)
- [x] Seed script (roles, admin, 4 volunteers, 3 locations, 6 activities)
- [x] Tailwind v4 standalone build script with theme colours
- [x] Unit tests (models, passwords, errors, logging) + integration tests (schema, constraints, health)
- [x] GitHub Actions CI (ruff, mypy, pytest on MySQL 8)
- [x] README with XAMPP setup and commands
- [ ] `docs/design/erd.png` and `docs/design/reference.png` added to the repo (needs the files)

## Phase 1: Authentication
- [ ] Volunteer sign-up (Pydantic validation, unique username/email, password rules) creates user + profile
- [ ] Login / logout with one generic error message
- [ ] Lockout after 5 failed attempts for 15 minutes; counter resets on success
- [ ] Inactive accounts blocked; role-based route protection (decorator + service check)
- [ ] Rate limit on login route
- [ ] Login page matches design (split screen)
- [ ] Tests + e2e login test

## Phase 2: Volunteer profile
- [ ] View / edit profile with validation
- [ ] Decide: "Forgot password?" and "Change Photo" now or later

## Phase 3: Admin activities and locations
- [ ] Locations CRUD
- [ ] Activities CRUD; delete with registrations sets CANCELLED
- [ ] Audit log on every create / update / delete / cancel

## Phase 4: Browse activities
- [ ] OPEN activities list with search + filters (date, location, keyword)
- [ ] Details page with computed available slots

## Phase 5: Register for an activity
- [ ] Checks: OPEN, not already registered, slots available
- [ ] Row lock (`with_for_update`) + single transaction; re-use cancelled row
- [ ] Notify admins

## Phase 6: Admin review
- [ ] Pending list; approve re-checks capacity; reject requires remarks
- [ ] reviewed_by / reviewed_at, notify volunteer, audit log

## Phase 7: My registrations, schedule, notifications
- [ ] Registration status list with tabs
- [ ] Cancel rules (PENDING/APPROVED and not started); notify admin + audit log
- [ ] Schedule + history; notifications with mark-as-read

## Phase 8: Reports and audit logs
- [ ] Reports: registrations per activity, volunteers per activity, totals by status
- [ ] CSV export; audit log viewer with filters

## Phase 9: Polish and deploy
- [ ] Responsive + accessible UI, empty/error/loading states
- [ ] Demo seed data, README screenshots, deployment guide
