# Plan: CRUD APIs for Departments, Majors, Sub-majors, and Students

## Ordered implementation steps

1. Update `AGENTS.md` with a task workflow distinction: small tasks may proceed
   without plan/confirmation; substantial tasks require their own
   `.agents/tasks/<task-slug>/task.md` and `plan.md`, followed by explicit
   approval.
2. Update `AGENTS.md` with a project-specific shared database exception:
   services may share the physical database file but retain exclusive logical
   ownership of their tables, do not directly query other services' tables, and
   use database-first unmanaged mappings unless an approved task authorizes a
   schema change.
3. Restore `database/DB_ProjectManagerment.db` from the verified
   `DB_ProjectManagerment.pre-academic-migration-20261009.db` backup to remove
   the code-first academic tables and migration history created in error.
4. Create `services/topic-service` as an independent Django service, including
   an isolated `venv`, `manage.py`, config package, service README, `.env.example`,
   copied `requirements.txt` from academic-service, and the `topic_manager`
   Django app (display name `topic-manager`).
5. Configure the service for port `8004`, register the future Consul identity
   `topic-service`, and add a public `GET /health/` endpoint. Update the root
   architecture documentation, gateway routing, and CI only after their
   corresponding integration is explicitly planned and approved.
6. Add a database-first `Topic` mapping to existing `Topics` with
   `Meta.managed = False`; do not create or run migrations. `MajorId` and
   `AdvisorId` remain opaque IDs.
7. Add explicit request/response DTOs, JWT authentication, and a Topic CRUD
   API. Read requires authentication; write requires JWT `role: 1`, matching
   the academic-service policy.
8. Add tests for health, JWT authorization, DTO validation, and database-first
   mappings. Run Django check/tests using topic-service's own environment.
9. Inspect the root and gateway READMEs, then update architecture diagrams,
   service/port tables, ownership notes, and route documentation to include
   topic-service.
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
- `services/topic-service/**`
- `services/academic-services/requirements.txt` (source only; unchanged)
- `README.md`
- `api-gateway/README.md`
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

# Current plan: Department CRUD handlers in app views (2026-10-10)

1. After explicit approval, inspect local test/settings conventions read-only.
2. Replace Department CRUD inheritance with explicit GenericAPIView-based
   list/create and detail classes in DeparmentManager/views.py. Preserve DTO
   handling and security.permissions.ReadOnlyOrRoleOneWrite; use the existing
   from_department conversion directly instead of runtime alias assignment.
3. Implement GET/POST only for the collection and GET/PUT/PATCH/DELETE only for
   details. Preserve URL patterns and successful response codes.
4. Expand DeparmentManager/tests.py for CRUD success, invalid payloads, missing
   objects, permission failures and detail POST 405, without production DB writes.
5. Run focused Department tests, then python manage.py check and python manage.py
   test in academic-services using its available environment. Review the diff.

## Expected changed files
- .agents/task.md and .agents/plan.md (current task sections)
- services/academic-services/DeparmentManager/views.py
- services/academic-services/DeparmentManager/tests.py

## Verification and rollback
Assert response DTOs/statuses and read/write permission policy; confirm other
apps still use unchanged shared CRUD. No inter-service clients are changed.
Undo only this task's view/test changes to roll back; no database rollback is
needed. No README changes are needed because paths, configuration and supported
CRUD contracts remain unchanged; detail POST is explicitly rejected.

## Revised implementation plan (supersedes current steps above)
1. After approval, inspect academic-service settings and test conventions.
2. Create DeparmentManager/services.py with Department list/get/create/update/
   delete operations. Keep record lookup, business operations and persistence
   here; use domain/model exceptions, with no DRF Response or HTTP dependency.
3. Refactor DeparmentManager/views.py into explicit collection/detail HTTP
   handlers. Preserve authentication and ReadOnlyOrRoleOneWrite. Validate input
   with request DTOs, call services, serialize results with response DTOs and
   translate missing records into 404. Remove runtime DTO alias assignment.
   Do not add ORM calls or business rules to views. Keep routes unchanged and
   return 405 for detail POST.
4. Expand DeparmentManager/tests.py with isolated service tests and view tests
   for delegation, CRUD responses, validation, missing records, authentication
   and role failures, plus detail POST 405. Never write the shared project DB.
5. Run focused tests, academic-service manage.py check and manage.py test using
   the available environment. Review changed files and report limitations.

Revised implementation files: DeparmentManager/services.py (new), views.py,
tests.py; planning files only before approval. Shared CRUD, models, DTO contracts,
URLs, infrastructure and database remain outside implementation scope.
Rollback: undo only these service/view/test changes, preserving other user work;
no schema or database rollback is necessary.

# Current plan: Services for Major, SubMajor and Student (2026-10-10)

1. After explicit approval, inspect the three apps' models and existing tests,
   plus local conventions, without changing models/schema.
2. Add services.py per app with list/get/create/update/delete operations and
   relationship validation. Define app-local business validation exceptions
   with field errors, independent of DRF and HTTP. Validate before persistence;
   Student updates use merged existing/proposed state.
3. Simplify request serializers to DTO field/type validation; remove ORM-based
   relationship checks now owned by services. Preserve response DTO contracts.
4. Refactor each views.py to explicit GenericAPIView collection/detail handlers,
   preserving permissions, validating DTOs and calling services. Translate
   missing records to 404 and service validation errors to 400; serialize results.
   Remove runtime response DTO aliases and inherited CRUD. Detail POST is 405.
5. Expand each app's tests.py with isolated service tests and endpoint tests:
   CRUD delegation, parent relationship failures, Student partial update cases,
   malformed payloads, missing records, token/role failures and detail POST 405.
6. Run focused tests for the three apps, then academic-service manage.py check
   and manage.py test using its existing venv. Review diff and changed-file scope.

## Expected files to change
- .agents/task.md, .agents/plan.md
- services/academic-services/MajorManager/{services.py,views.py,serializers.py,tests.py}
- services/academic-services/SubMajorManager/{services.py,views.py,serializers.py,tests.py}
- services/academic-services/StudentManager/{services.py,views.py,serializers.py,tests.py}

## Verification and rollback
Test service behavior and HTTP responses with no shared project DB writes.
Re-run Department tests as part of the full suite. No inter-service client is
changed. No README change is needed because deployed architecture, URLs, DTOs
and configuration are preserved. Roll back only these task-specific source/test
edits; no database restore or migration is required. Approval pending.

# Current plan: Docker Desktop and gateway startup (2026-10-10)

1. After approval, launch the existing Docker Desktop executable with
   Start-Process -WindowStyle Hidden; do not start containers before approval.
2. Poll docker info with short bounded waits, providing progress updates. If
   startup fails, inspect local diagnostics read-only; do not reset/install.
3. From api-gateway, validate docker compose config, then docker compose up -d
   using the current desktop-linux context and existing configuration.
4. Verify docker compose ps, container logs and docker compose exec -T
   api-gateway nginx -t. Probe local port 8000/auth/health/ if auth is running;
   report upstream unavailability separately from Docker engine startup.

## Expected writes and verification
Only .agents/task.md and .agents/plan.md are repository changes. Docker Desktop
may update its runtime state; Compose may fetch the existing image and create/
start the gateway container/network. No code changes, so no new automated tests
are needed; use runtime checks above.

## Rollback
Stop only the gateway started by this task if requested; do not remove volumes
or affect unrelated containers. Leave existing Docker data/configuration intact.
Do not shut down Docker Desktop automatically if other workloads are running.

# Current plan: Remove password hash verification from login (2026-10-10)

1. After explicit approval, replace check_password in authentication/views.py
   with hmac.compare_digest on supplied/stored password UTF-8 bytes. Preserve
   user lookup, error response and JWT issuance; no secret logging.
2. Expand authentication/tests.py using mocked Users lookups to verify login
   via accepted identifiers, exact password comparison (including whitespace/
   Unicode), wrong password, missing user, invalid fields, safe response DTOs,
   signed JWT claims, token refresh and authenticated profile behavior.
3. Update root README.md and services/auth-service/README.md to document
   plaintext comparison, unchanged JWT requirements and the production risk.
4. Run auth-service venv python manage.py check and python manage.py test.
   Review diff scope and confirm no database/configuration changes.

## Expected changed files
- .agents/task.md, .agents/plan.md
- services/auth-service/authentication/views.py
- services/auth-service/authentication/tests.py
- services/auth-service/README.md
- README.md

## Verification and rollback
Only mocked accounts are used in tests. Keep existing Consul tests passing.
No live login calls are needed before approval or for verification. Rollback
only this task's view/test/documentation edits to restore check_password; no
DB rollback is needed because no stored values are modified.

# Current plan: Per-service .env loading (2026-10-10)

1. After explicit approval, verify a compatible python-dotenv release using
   official package metadata. Add a pinned version to the two requirements.txt
   files and install only in the corresponding existing venvs.
2. In both config/settings.py files, import load_dotenv and call
   load_dotenv(BASE_DIR / '.env', override=False) immediately after BASE_DIR,
   before reading any environment-backed configuration.
3. Add config/tests.py in each service using temporary settings/.env fixtures
   and isolated subprocess environments. Cover quoted JWT values, different
   working directories, environment precedence, missing file and auth Consul
   parsing. Use dummy secrets and never overwrite actual .env files.
4. Update root README, auth README and academic README with .env locations,
   environment precedence, installation/restart instructions and shared JWT key
   requirement. Do not put real secrets into documentation.
5. Run focused settings tests then both service manage.py check and manage.py
   test using their venvs. Set CONSUL_AUTO_REGISTER=false only in verification
   child processes. Verify resulting keys agree without printing secret values
   if actual .env files exist; do not restart servers automatically.
6. Review CI: current matrix installs each service requirements and runs full
   checks/tests, so no workflow change is expected unless commands must change.

## Expected files to change
- .agents/task.md, .agents/plan.md
- services/{auth-service,academic-services}/requirements.txt
- services/{auth-service,academic-services}/config/settings.py
- services/{auth-service,academic-services}/config/tests.py (new)
- services/{auth-service,academic-services}/README.md
- README.md

## Verification and rollback
No real DB writes, containers or live API requests are needed. Runtime Consul
registration is disabled in verification processes. Roll back only task-specific
settings/test/dependency/documentation edits; remove the added package from these
venvs if requested, without disturbing existing dependencies. No schema rollback.
Approval pending.

# Current plan: Implement LectureManager (2026-10-10)

1. After explicit approval, create LectureManager/__init__.py and apps.py;
   register LectureManager in academic config/settings.py.
2. Add unmanaged Lecturer model with explicit Lecturers mapping, string PK and
   nullable Department ForeignKey. Do not create a Users model/relation or any
   migration. Preserve database constraints and DO_NOTHING deletion behavior.
3. Add explicit request/response DTO serializers with lecturer_id (nonblank,
   string) and optional nullable department_id. Responses exclude identity data.
4. Add services.py with list/get/create/update/delete, academic Department
   existence validation and primary-key immutability. Wrap writes in transactions
   and translate IntegrityError to business validation exceptions; never expose
   raw schema/SQL. No direct auth or Topics access.
5. Add explicit views.py calling services, with existing ReadOnlyOrRoleOneWrite
   and default AcademicJWTAuthentication. Map service validation to 400 and
   missing Lecturer to 404. Add urls.py using lecturers and string detail IDs;
   include under existing /api/ in config/urls.py.
6. Add LectureManager/tests.py for mapping, DTOs, CRUD, parent validation,
   duplicate/integrity failures, unchanged vs changed PK, delete constraints,
   service delegation, missing resources, JWT failure and role policy. Use mocks
   and/or isolated temporary/in-memory storage; never write the shared DB.
7. Update root and academic READMEs with ownership, endpoint table, example JSON,
   JWT role requirements, error expectations and identity-validation limitation.
8. Run focused LectureManager tests, academic manage.py check and full manage.py
   test with existing venv. Review diff; current CI auto-discovers tests and
   installs unchanged dependencies, so no workflow edit is expected.

## Expected changed files
- .agents/task.md and .agents/plan.md
- services/academic-services/LectureManager/{__init__.py,apps.py,models.py,
  serializers.py,services.py,views.py,urls.py,tests.py}
- services/academic-services/config/{settings.py,urls.py}
- services/academic-services/README.md and README.md

## Verification and rollback
Assert SQL mapping/column metadata, all HTTP methods and supported JSON fields,
string ID routing, local JWT auth, role authorization and safe validation/errors.
No new cross-service client requires failure/retry tests. No live requests or
Consul registration are needed for verification. Roll back only LectureManager
files and its settings/URL/documentation additions, preserving earlier edits;
no database restore/migration rollback. Approval pending.
