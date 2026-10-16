# Software Requirements Specification: traceability

This table maps every requirement from the project brief to the code and tests that
satisfy it. Rows marked *planned* point to the phase that will deliver them.
Updated at the end of every phase.

## Functional requirements

| ID | Requirement | Where it is covered | Tests |
|---|---|---|---|
| FR-1 | Users must log in with username and password before accessing any module. | *Planned: Phase 1* (`app/controllers/auth.py`, `app/services/auth_service.py`, `app/auth/`) | *Phase 1* |
| FR-2 | Role-based access control (Admin vs Volunteer). | Roles are reference data in `database/schema.sql`; `Person.is_admin` in `app/models/person.py`; `UserDAO.to_model()` returns `Admin` or `Volunteer`. *Planned: Phase 1* route decorators in `app/auth/decorators.py` and service checks. | `tests/unit/test_dao.py::test_user_dao_builds_admin_without_profile` |
| FR-3 | Authorized users can Create, Read, Update and Delete core records. | DAO write methods in `app/dao/` (`insert`, `update`, `delete`, `set_status`). *Planned: Phases 2, 3* for the screens. | `tests/unit/test_dao.py`, `tests/integration/test_database.py::test_user_and_profile_round_trip` |
| FR-4 | All input is validated before it is saved. | `Activity.validate()` in `app/models/activity.py`; database CHECK constraints in `database/schema.sql`. *Planned: Phase 1+* Pydantic schemas in `app/schemas/`. | `tests/unit/test_models.py::test_activity_validate_rejects_bad_rules`, `tests/integration/test_database.py::test_check_constraint_becomes_validation_error` |
| FR-5 | All core data is stored in MySQL served through XAMPP. | `database/schema.sql` (8 InnoDB tables); `app/database/db_manager.py`; `scripts/init_db.py`. | `tests/integration/test_database.py::test_schema_has_all_tables_with_innodb_utf8mb4` |
| FR-6 | Every add/edit/delete is recorded in an audit trail. | `audit_logs` table; `AuditLogDAO` in `app/dao/audit_log_dao.py`. *Planned: Phases 3, 6, 7* write the entries. | `tests/unit/test_dao.py::test_audit_insert` |
| FR-7 | At least one summary report, on screen and exportable (CSV + printable). | `BaseReport` template method in `app/services/reports/base_report.py`; `VolunteerActivityReport` and `SystemTotalsReport` in `person_reports.py`. *Planned: Phase 8* for screens, CSV and print view. | `tests/unit/test_reports.py`, `tests/unit/test_models.py::test_volunteer_generate_report_counts_own_hours` |
| FR-8 | Errors are handled without crashing: invalid input, lost database connection, duplicate entries. | `translate_error()` in `app/database/db_manager.py` maps MySQL errors to typed errors in `app/errors.py`; `register_error_handlers()` in `app/__init__.py` renders `templates/errors/error.html` (503 says "Is MySQL running in XAMPP?"). | `tests/unit/test_db_manager.py::test_translate_error_maps_mysql_codes`, `tests/integration/test_database.py::test_duplicate_username_becomes_conflict_error`, `::test_lost_connection_becomes_database_error`, `::test_health_shows_friendly_page_when_database_is_down` |

## Non-functional requirements

| Quality | Requirement | Where it is covered |
|---|---|---|
| Usability | Main actions within 2 clicks of the dashboard, no manual needed. | *Planned: Phase 1* base layout with sidebar; dashboards link straight to each action. |
| Reliability | Full 15-minute demo without unhandled crashes. | Typed errors + global handlers (`app/__init__.py`); reconnect in `DatabaseManager.connection()`. *Phase 9* demo checklist. |
| Performance | CRUD on 1,000 records within 2 seconds. | Indexes on every FK and on `activity_date`, `status`, `title`, `timestamp` (`database/schema.sql`); `LIMIT/OFFSET` pagination in `ActivityDAO.search()`; `python seed.py --big` creates 1,000 activities for the check. |
| Security | No plain-text passwords; all SQL parameterized. | bcrypt cost 12 in `app/auth/passwords.py`; every DAO uses `%s` placeholders (`tests/unit/test_dao.py::test_user_dao_insert_sets_id_and_binds_values` proves injection text stays a parameter); `Person.to_dict()` strips the hash. |
| Maintainability | Modules: models, views, controllers, dao, database; PEP 8 naming. | Folder layout in `README.md`; `ruff` enforces PEP 8 (`N` rules) and `mypy --strict` checks types in CI. |
| Portability | Runs on any machine with Python 3 and XAMPP via the README; no hard-coded paths. | All settings come from `.env`; `scripts/init_db.py` and `scripts/tailwind.ps1` use relative paths. |

## Required design patterns

| Pattern | Class / file | Test that exercises it |
|---|---|---|
| Singleton | `DatabaseManager` in `app/database/db_manager.py` | `tests/unit/test_db_manager.py::test_singleton_returns_the_same_instance` |
| MVC | `app/models/`, `app/templates/`, `app/controllers/` | `tests/integration/test_database.py::test_health_endpoint_reaches_database` |
| Inheritance | `BaseEntity` -> `Person` (abstract) -> `Volunteer`, `Admin` in `app/models/` | `tests/unit/test_models.py::test_person_cannot_be_instantiated_directly` |
| Polymorphism | `Person.generate_report()` overridden by `Volunteer` and `Admin` | `tests/unit/test_models.py::test_volunteer_generate_report_counts_own_hours`, `::test_admin_generate_report_gives_system_totals` |
| Template Method | `BaseReport.generate()` in `app/services/reports/base_report.py` | `tests/unit/test_reports.py::test_generate_runs_steps_in_fixed_order` |
| DAO | One class per table in `app/dao/` | `tests/unit/test_dao.py` (happy + failure per DAO) |
