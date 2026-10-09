# Plan: CRUD APIs for Departments, Majors, Sub-majors, and Students

## Ordered implementation steps

1. Update `AGENTS.md` with a project-specific shared database exception:
   services may share the physical database file but retain exclusive logical
   ownership of their tables, do not directly query other services' tables, and
   use database-first unmanaged mappings unless an approved task authorizes a
   schema change.
2. Restore `database/DB_ProjectManagerment.db` from the verified
   `DB_ProjectManagerment.pre-academic-migration-20261009.db` backup to remove
   the code-first academic tables and migration history created in error.
2. Inspect the restored database schema read-only and record existing academic
   table names, primary keys, columns, relationships, and constraints.
   Result: map public `departments` to `Faculties`, `majors` to `Majors`,
   `sub-majors` to `Specializations`, and `students` to `Students`.
3. Configure academic-service's database connection to use
   `database/DB_ProjectManagerment.db`, while preserving its model ownership
   boundary and avoiding all auth-service table access.
4. Replace code-first models with database-first mappings using `managed =
   False`, explicit `db_table`/`db_column` values, string primary keys, and no
   migration creation or application. `StudentId` remains an opaque ID and
   must not cause a query to the `Users` table.
5. Establish a shared `JWT_SIGNING_KEY` environment configuration in
   auth-service and academic-service, configure Simple JWT to use it, and add
   a non-committed example entry to each relevant environment template.
6. Enable Django REST Framework and register the four existing academic apps.
   Add an academic-service JWT authentication class that verifies signature and
   expiry locally and exposes token claims without querying auth-service.
   Add a reusable permission class that permits all authenticated callers to
   read and permits only the integer role claim `1` to write.
7. Define DTO validation for the existing hierarchy:
   `Faculty -> Major -> Specialization`, and `Student -> Major/Specialization`.
   Preserve database-side referential integrity; do not create/alter any
   schema constraint.
8. Add dedicated request and response DTO serializers (not direct model
   serialization), including validation that a supplied sub-major belongs to
   the student's supplied major.
9. Add viewsets and per-app URL modules; mount them in `config/urls.py` under
   `/api/` with plural resources:
   `departments`, `majors`, `sub-majors`, and `students`.
10. Add API tests for create/list/retrieve/update/delete, uniqueness and
   relationship validation, HTTP 404 behavior, missing/invalid JWT (`401`),
   read access for a valid non-1 role, and write denial for a valid JWT role
   other than `1` (`403`).
11. Document endpoint methods, database-first field mappings, relationships, required bearer
   authentication and role `1`, plus error/status
   expectations.
12. Run `python manage.py check` and `python manage.py test` from
   `services/academic-services`; report any pre-existing failures separately.
13. Commit each manager app independently after its mapping and tests pass;
    commit the academic-service API README after the app commits.

## Expected files to change

- `.agents/task.md`, `.agents/plan.md`
- `AGENTS.md`
- `services/auth-service/config/settings.py`, `.env.example`
- `services/academic-services/config/settings.py`, `config/urls.py`
- `services/academic-services/config/settings.py` (shared database path)
- `services/academic-services/.env.example`
- `services/academic-services` JWT authentication/permission module
- `services/academic-services/{DeparmentManager,MajorManager,SubMajorManager,StudentManager}/models.py`
- `services/academic-services/{DeparmentManager,MajorManager,SubMajorManager,StudentManager}/serializers.py`
- `services/academic-services/{DeparmentManager,MajorManager,SubMajorManager,StudentManager}/views.py`
- `services/academic-services/{DeparmentManager,MajorManager,SubMajorManager,StudentManager}/urls.py`
- `services/academic-services/{DeparmentManager,MajorManager,SubMajorManager,StudentManager}/tests.py`
- Existing academic migration files will be removed from source control; no new
  migration files will be created for database-first mappings
- `services/academic-services/README.md` (and root `README.md` only if route
  documentation needs extending)

## Verification

- Execute Django system checks.
- Execute academic-service tests, including all four app test modules.
- Confirm response codes and validation behavior via the Django REST Framework
  test client.
- Confirm any signed access token can read, only `role: 1` can write, another
  valid role receives `403` on writes, and malformed/expired tokens receive
  `401`.
- Confirm all mapped tables and columns match the restored shared database and
  `makemigrations --check` reports no planned model migration.

## Rollback

- Restore the pre-migration backup before any database-first work. No schema
  migrations are permitted in this task; rollback code mappings through Git
  commits without altering the shared database.
