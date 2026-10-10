# Task: CRUD APIs for academic master data and students

## Objective

Implement protected Django REST Framework CRUD APIs in `academic-service` for
Departments, Majors, Sub-majors (specializations), and Students.

Update repository agent guidance to explicitly allow the project-approved
shared physical database and database-first Django model mappings.

Update the task-workflow rules so clearly scoped small changes do not require a
task/plan document or user confirmation, while every substantial task uses its
own directory under `.agents/tasks/<task-slug>/` containing `task.md` and
`plan.md`.

Create a standalone `services/topic-service` for Topic ownership. It will use
its own Python virtual environment and begin with an exact copy of
`services/academic-services/requirements.txt`.

The Django app inside this service will be named `topic-manager` (Python module
`topic_manager`).

Update the root README and API Gateway README to describe the architecture
after Topic ownership moves to `topic-service`.

## Scope

- Use database-first Django model mappings for the existing academic tables in
  `database/DB_ProjectManagerment.db`; do not create or apply academic schema
  migrations.
- Update `AGENTS.md` with the approved exceptions and guardrails for shared
  database use and database-first development.
- Update `AGENTS.md` with the task-size exception and per-task planning-folder
  convention.
- Create a Django `topic-service` scaffold with its own configuration, health
  endpoint, database-first Topic mapping, and separate virtual environment.
- Create the `topic_manager` Django app as the owner of Topic API code.
- Update `README.md` and `api-gateway/README.md` with the topic-service port,
  route, ownership boundary, shared database/database-first policy, and JWT
  access expectations.
- Copy the academic-service dependency manifest into topic-service without
  changing dependency versions.
- Add explicit DRF serializers, viewsets, and app URL modules.
- Expose the APIs beneath the academic-service path `/api/` (the API
  Gateway's existing `/academic/*` prefix forwards requests to this service).
- Register the four existing Django apps and DRF in Django settings.
- Add endpoint tests for CRUD success, validation errors, and missing records.
- Integrate local JWT signature/expiry validation with `auth-service`; require
  a JWT for every endpoint and restrict write operations to tokens whose
  `role` claim equals integer `1`.
- Move JWT signing configuration in both services to one shared environment
  variable; no signing key will be committed to source control.
- Document the API contract in the academic-service README (create it if absent)
  and update the root README only if needed for the new route documentation.
- Keep dedicated request/response DTO serializers rather than using model
  serializers as the public request/response contract.
- Create a separate Git commit for each implemented manager app, including its
  model, serializer DTOs, view, routes, tests, and migration. Shared academic
  configuration will be committed with the first app that needs it.
- Configure academic-service to use the repository shared SQLite database at
  `database/DB_ProjectManagerment.db`, matching auth-service's physical
  database location. Academic-service retains logical ownership of its own
  tables and must not query auth-service's `Users` table.

## Proposed data model assumptions

- The inspected database-first schema maps public resource `departments` to
  existing table `Faculties` (`FacultyId`, `FacultyName`); this mapping is a
  naming adaptation, not a new database table.
- `majors` maps to `Majors` (`MajorId`, `MajorName`, `FacultyId`).
- `sub-majors` maps to `Specializations` (`SpecializationId`,
  `SpecializationName`, `MajorId`).
- `students` maps to `Students` (`StudentId`, `MajorId`, `SpecializationId`,
  `AccumulatedCredits`, `GPA`). `StudentId` is the existing primary key and a
  foreign key to `Users`; academic-service will treat it as an opaque ID and
  will not query the `Users` table.
- The existing app spelling `DeparmentManager` is preserved to avoid breaking
  repository imports; its public API resource is correctly spelled
  `departments`.

## Constraints

- Respect academic-service ownership; no access to another service database or
  models and no inter-service call is required for this local master data.
- Use JSON DTOs through DRF serializers; do not expose models directly.
- Use safe standard REST status codes and no sensitive data in responses.
- Do not change fixed service ports, gateway prefixes, dependencies,
  dependencies, infrastructure, or unrelated services.
- A shared physical database is an explicit user-approved exception to the
  normal database-per-service SOA guideline. It does not authorize direct
  cross-service ORM access: each service remains limited to its owned tables.
- Database-first mappings must set explicit `db_table`/`db_column` metadata and
  `managed = False`; schema-altering migrations are prohibited unless a later
  approved task explicitly authorizes them.
- A small task means a narrowly scoped, low-risk change that does not alter
  application behavior, API contracts, models/database/schema, dependencies,
  infrastructure, security/authorization, CI, or documentation affecting users
  or operators. If uncertain, treat the task as substantial.
- topic-service owns the existing `Topics` table in the shared database;
  academic-service must stop owning or directly accessing that table after the
  service split is complete. Topic relationships such as `MajorId` and
  `AdvisorId` are opaque IDs and must not cause cross-service ORM access.
- `auth-service` already issues access tokens containing `user_id`, `email`,
  and `role`. The academic service will validate token signature and expiry
  locally; it will not query the auth-service database or call `/me/` per
  request.
- All CRUD methods for all four resources require `Authorization: Bearer
  <access-token>`. Any authenticated role may use read-only `GET` methods.
  `POST`, `PUT`, `PATCH`, and `DELETE` require role `1`. Missing, invalid, or
  expired tokens return `401`; a valid token with another role attempting a
  write returns `403`.
- `GET /health/` will remain public when it is added as part of the
  academic-service operational contract.

## Acceptance criteria

- Collection and detail endpoints exist for departments, majors, sub-majors,
  and students; each supports list, retrieve, create, partial/full update, and
  delete.
- Relationship and uniqueness validation returns HTTP 400 with serializer
  errors; unknown IDs return HTTP 404.
- Every CRUD route rejects unauthenticated callers with `401 Unauthorized`.
  Any authenticated role may read; writes by a role other than `1` return
  `403 Forbidden`.
- The API is accessible under `/api/` in the academic service and can be
  reached through the existing gateway as `/academic/api/`.
- Automated tests cover normal CRUD, invalid payloads, and missing detail
  resources; Django checks and the relevant test suite pass.

## Proposed endpoint contract

The following are paths inside `academic-service`; through the API Gateway,
prepend `/academic` (for example, `GET /academic/api/departments/`).

| Resource | Method | Service path | Purpose | Success status |
| --- | --- | --- | --- | ---: |
| Department | GET | `/api/departments/` | List departments | 200 |
| Department | POST | `/api/departments/` | Create a department | 201 |
| Department | GET | `/api/departments/{id}/` | Retrieve a department | 200 |
| Department | PUT/PATCH | `/api/departments/{id}/` | Replace/update a department | 200 |
| Department | DELETE | `/api/departments/{id}/` | Delete a department without dependents | 204 |
| Major | GET | `/api/majors/` | List majors | 200 |
| Major | POST | `/api/majors/` | Create a major for a department | 201 |
| Major | GET | `/api/majors/{id}/` | Retrieve a major | 200 |
| Major | PUT/PATCH | `/api/majors/{id}/` | Replace/update a major | 200 |
| Major | DELETE | `/api/majors/{id}/` | Delete a major without dependents | 204 |
| Sub-major | GET | `/api/sub-majors/` | List sub-majors | 200 |
| Sub-major | POST | `/api/sub-majors/` | Create a sub-major for a major | 201 |
| Sub-major | GET | `/api/sub-majors/{id}/` | Retrieve a sub-major | 200 |
| Sub-major | PUT/PATCH | `/api/sub-majors/{id}/` | Replace/update a sub-major | 200 |
| Sub-major | DELETE | `/api/sub-majors/{id}/` | Delete a sub-major without students | 204 |
| Student | GET | `/api/students/` | List students | 200 |
| Student | POST | `/api/students/` | Create a student | 201 |
| Student | GET | `/api/students/{id}/` | Retrieve a student | 200 |
| Student | PUT/PATCH | `/api/students/{id}/` | Replace/update a student | 200 |
| Student | DELETE | `/api/students/{id}/` | Delete a student | 204 |

All collection/detail endpoints return `400` for invalid or duplicate DTO
fields, and detail endpoints return `404` for an unknown `{id}`. Deletion of a
referenced academic entity returns a safe validation error instead of cascading
data loss. Every endpoint listed in the table requires a bearer access token.
`GET` is available to every authenticated role; writes require JWT claim
`role: 1`.

## Risks

- The prior code-first migration implementation must be rolled back by
  restoring the verified pre-migration database backup before database-first
  mapping is introduced. No existing database schema may be altered.
- SQLite permits only limited concurrent writes. Sharing its single file
  between independently running services can cause locking contention and
  couples backup/restore operations. A production deployment should prefer a
  server database with separate schemas/credentials, or separate databases.
- Deleting a Department/Major with dependent objects needs an explicit
  protection policy; the planned implementation will use `PROTECT` and surface
  a safe validation response rather than cascade-delete academic records.
- Public `departments` terminology differs from the table name `Faculties`,
  which can be confusing for clients. The proposed compatibility mapping must
  be explicitly approved before implementation.

# Current task: Department CRUD handlers in app views (2026-10-10)

## Objective and scope
Move Department CRUD HTTP handlers from inherited security.crud classes into
DeparmentManager/views.py so the resource behavior is visible in its own app.
Only Department views and their automated tests are implementation scope.

## Constraints
Preserve existing URLs, DTO fields, response statuses, JWT authentication and
ReadOnlyOrRoleOneWrite policy. Keep shared security/crud.py for other apps.
Do not modify models, database files/schema, migrations, dependencies,
infrastructure, service ports or gateway routes. No external calls.

## Acceptance criteria
Department list/create and detail GET/PUT/PATCH/DELETE handlers are explicit in
DeparmentManager/views.py without inheriting shared CRUD views. Detail POST
returns 405 rather than inheriting the collection creation handler. Existing
supported CRUD behavior and permissions remain covered by automated tests.
Django checks and academic-service tests run; failures are reported accurately.

## Assumptions and risks
The request means moving HTTP handlers, not changing endpoint paths. Existing
<int:pk> routes and string database IDs are a pre-existing mismatch and remain
outside this refactor. Moving handlers can accidentally change DTO conversion
or permissions; focused tests will guard both. Tests must use mocks or isolated
test storage and never write the shared project database. Detail POST 405 is an
intentional correction to method handling and must be included in approval.

## Revised scope: Department application service (supersedes the current scope above)
The user requests a services.py layer inside DeparmentManager. This is an
application service module, not a new independently deployed SOA service.
Department views handle HTTP input/output, request DTO validation and existing
permissions; they delegate business operations and all ORM access to services.py.
The service provides list, get, create, update and delete operations, including
record lookup and persistence. Keep request/response DTOs independent of models;
the service must not depend on HTTP requests, Response or HTTP status codes.
No new domain rules are assumed or introduced in this structural refactor.

Additional acceptance criteria: views contain no direct ORM operations and do
not inherit security.crud CRUD handlers. Service functions are covered by tests;
view tests verify delegation, responses, validation and authorization. Missing
records map to 404 at the HTTP boundary. Preserve existing URLs and permissions.
Additional implementation file: DeparmentManager/services.py. Other exclusions
and the planned detail POST 405 correction remain in effect. Approval pending.

# Current task: Application services for remaining academic apps (2026-10-10)

## Objective and scope
Apply the Department URL -> view -> application service -> model structure to
MajorManager, SubMajorManager and StudentManager inside academic-service.
Create services.py per app; move CRUD ORM operations and relationship business
validation there. Keep request DTO shape/type validation and response conversion
in the HTTP layer. This does not create new deployed SOA services.

## Constraints
Preserve DTO fields, routes, JWT authentication, role-1 write policy, service
ports and data ownership. No access to auth Users. No model/schema/database,
migration, dependency, CI or infrastructure changes. Keep Department and shared
security/crud.py unchanged. Do not add new business rules.

## Acceptance criteria
Views have explicit CRUD HTTP methods and delegate operations to app services;
no direct ORM or relationship business validation in views/serializers.
Services validate optional parent references for Major/SubMajor and the required
Major and matching optional SubMajor for Student. Partial updates validate the
merged current/proposed state. Service errors map to existing field-based 400
responses; missing records map to 404. Detail POST returns 405. Tests cover CRUD,
validation, partial updates, missing records, authentication and authorization.
Academic-service Django check and full tests pass or limitations are reported.

## Assumptions and risks
The request covers the three remaining resource apps, not config/security.
Services are local application modules and may access academic-owned models.
Student PATCH currently relies on serializer.instance for omitted fields; the
new service must preserve existing values and relationship checks. Keep the
pre-existing integer URL converters despite string model IDs; route correction
is outside scope. Tests use mocks/isolated storage, never the shared project DB.
Moving validation can alter error behavior; preserve field keys/messages and
check safe 400/404 responses. No new external-service contracts are introduced.

# Current task: Restore local Docker engine and start API Gateway (2026-10-10)

## Objective and scope
Resolve docker compose up -d failing because Docker Desktop Linux Engine's
named pipe is unavailable, then start the existing API Gateway container.
Read-only inspection found desktop-linux selected, Docker CLI installed,
Docker Desktop executable present, no Docker Desktop/backend processes, and
com.docker.service stopped. Existing Compose uses nginx:1.27-alpine, port 8000.

## Constraints and acceptance criteria
Do not edit Compose, nginx configuration, service ports, source, dependencies,
database or migrations. Do not reset Docker, delete volumes/images/containers
or change engine mode/context without a revised plan. After approval, launch
Docker Desktop and use the existing Linux engine/context. Success: docker info
can reach the server, docker compose up -d succeeds, the gateway is running and
its nginx configuration passes nginx -t. Backend availability is verified only
if the corresponding Django processes are running.

## Assumptions and risks
Docker Desktop is stopped rather than broken. Starting it can resume existing
containers and consume local resources. Compose may download the configured
image. A WSL/virtualization or privilege error would require additional diagnosis
and possibly a revised approved plan. Existing port 8000 conflicts must be
reported, not resolved by terminating unrelated processes. Approval pending.

# Current task: Plaintext password comparison for login (2026-10-10)

## Objective and scope
At the user's explicit request, replace Django check_password in auth-service
login with direct comparison against the existing Users.Password value.
Use constant-time comparison of UTF-8 bytes; do not hash the supplied password.
This changes password verification only, not JWT signing or validation.

## Constraints
No database writes, password conversion, schema change, migrations, package
installation, infrastructure or other-service changes. Preserve existing login
DTOs, routes, token claims, refresh and profile behavior. Never log or return
passwords. Only repository planning files may change until approval.

## Acceptance criteria
An existing plaintext password authenticates when supplied exactly; wrong
password and unknown user retain the same safe 401 response. Missing/invalid
fields return 400. Successful login still issues usable signed access/refresh
JWTs and excludes passwords from its response. Tests cover identifier/email/
userid login, invalid credentials, DTO errors and token/profile behavior.
Run auth-service manage.py check and full tests; document the verification
policy in the root and auth-service READMEs.

## Assumptions and risks
The user wants plaintext comparison for the project, not a hash migration or a
fallback mode. Plaintext storage exposes passwords to anyone who reads the DB;
it is unsuitable for production. Existing hashed rows will no longer accept
original plaintext passwords with this policy; no rows will be changed or
converted. JWT hashing/signing configuration remains unchanged. Tests use fake
users and mocked ORM, never the shared project DB. Approval pending.

# Current task: Load local .env in auth and academic services (2026-10-10)

## Objective and scope
Automatically load services/auth-service/.env and
services/academic-services/.env during settings initialization, before reading
JWT_SIGNING_KEY and Consul options. The same JWT key in both files must be used
without manual PowerShell environment assignment. Scope is these two services.

## Constraints
Use python-dotenv with an explicit BASE_DIR / '.env' path and override=False:
existing process environment wins over file values. Missing .env is allowed
for CI/deployment. Preserve all API routes, JWT validation, authorization and
password policy. Do not edit/read out real secret values or commit .env files.
No database, migration, infrastructure or unrelated-service changes.

## Acceptance criteria
Each service loads only its own .env, independent of working directory.
Quoted values are parsed correctly, environment overrides remain intact, absent
files do not prevent startup, and settings consume loaded JWT/Consul values.
Add automated settings tests with temporary files/fake secrets; do not contact
Consul or write the shared DB. Both service checks and full tests pass. Existing
CI installs dependencies from per-service requirements without command changes.

## Assumptions and risks
Only auth-service and academic-service are requested by the current issue;
topic and other services remain outside scope. Add python-dotenv to both
requirements and install in their existing virtual environments after approval.
Pin a compatible published version verified after approval. File changes need
server restart. Stale shell JWT values override .env intentionally. Loading
auth .env can enable existing CONSUL_AUTO_REGISTER=true on actual server startup;
verification must disable this in test/check processes to avoid external calls.

# Current task: LectureManager lecturer CRUD app (2026-10-10)

## Objective and scope
Create the user-named LectureManager Django app inside academic-services using
URL -> explicit view -> application service -> database-first model, matching
the existing manager pattern. Resource/model terminology is Lecturer/lecturers.

## Inspected schema and ownership
Read-only sqlite metadata confirms Lecturers(LecturerId TEXT primary key,
FacultyId TEXT nullable). FacultyId references Faculties.FacultyId; LecturerId
references auth-owned Users.UserId. Academic owns Lecturers and Faculties only.
Map lecturer_id explicitly to LecturerId as a string primary key, department
relation explicitly to FacultyId with nullable metadata; managed=False.
Do not import/query Users, include identity fields or inspect private auth rows.

## API scope and acceptance criteria
Expose collection /api/lecturers/ with GET/POST and detail
/api/lecturers/<str:pk>/ with GET/PUT/PATCH/DELETE; gateway URLs prepend /academic.
Use request/response DTOs with lecturer_id and optional nullable department_id.
JWT required for every endpoint; all authenticated roles may read, writes
require role 1. Preserve existing services/routes and shared JWT configuration.
Services own CRUD and parent validation, views own DTO/HTTP translation.
Return 200/201/204 success, field-based 400 validation/integrity errors, 404
missing records, 401 invalid/missing/expired tokens, 403 unauthorized writes,
and 405 unsupported methods (including detail POST). Reject duplicate lecturer
IDs; lecturer_id is immutable on update (same value allowed, changed value 400).
No accidental creation from a changed primary key. Use safe messages for missing
referenced user / constraints without exposing raw database errors.

## Constraints, assumptions and risks
No schema change, production DB writes, migrations, packages, containers, CI
command changes or new deployed service. No changes to other managers. Existing
Users FK stays enforced by SQLite; no reusable service-authenticated identity
lookup contract is introduced. Caller supplies an existing user ID; the new app
does not independently validate identity via REST, an explicitly documented
limitation rather than cross-service ORM access. Do not infer lecturer identity
or role from a client-supplied ID. Existing foreign key dependencies can block
delete; handle safely with 400 rather than cascading or raw 500. SQLite concurrent
writes can contend; this task adds no retries/schema changes. No backup/DB
rollback is needed because the task never modifies the shared DB. Leave existing
unrelated working-tree changes (frontend, auth, etc.) untouched. Approval pending.

# Current task: Consul-discovered API Gateway (2026-10-10)

## Objective and scope
Connect api-gateway to Consul Service Registry so routes resolve healthy service
instances at runtime instead of fixed backend host/port proxy_pass entries.
Keep Nginx as the HTTP gateway. Add a small Python-standard-library discovery
worker in the gateway container to query Consul, generate upstream config,
validate it with nginx -t and reload only when routing changes.
Complete registry plumbing for academic-service, regist-service and topic-service;
auth-service already has health and registration. No domain APIs are introduced.

## Public contracts and architecture
Preserve gateway port 8000, Consul 8500 and backend ports/names auth-service:8001,
academic-service:8002, regist-service:8003, topic-service:8004. Preserve /auth/,
/academic/, /registrations/ stripping semantics and implement the /topics/ route
already documented in README. Forward Authorization, query strings and standard
proxy headers. Gateway health stays public. Service-owned JWT/role checks stay
unchanged. No cross-service ORM imports, domain models, password-policy changes
or database operations. Existing regist-service business APIs are not implemented
by this task; discovery does not make that service feature-complete.

## Acceptance criteria
Query Consul GET /v1/health/service/{name}?passing=true using configurable registry
URL and optional token. Use returned service/node address and service port only;
no hidden fixed backend fallback. Support multiple healthy instances. Validate
registry response addresses/ports before generating config. Registry requests
have bounded timeouts; refresh periodically, log no tokens. No healthy service
returns safe JSON 503. Registry outage retains last good data only for a bounded
configurable TTL, then fails closed with 503; startup works with Consul unavailable.
Nginx reloads only validated configuration, keeps existing requests running, uses
bounded proxy timeouts and does not blindly retry writes. Unknown routes return
safe 404. Discovery tracks healthy-instance address changes without image rebuild.

Every routed service has GET /health/ and opt-in, non-blocking Consul registration
with unique configurable instance ID, health checks and unhealthy deregistration.
New registration workers use bounded retry/backoff to recover registry startup
races without blocking requests; admin/test commands must not register. Existing
auth behavior is preserved unless minimal test/config fixes are needed.
Environment ALLOWED_HOSTS supports host.docker.internal for container health
checks, without wildcard host acceptance. Document bind address 0.0.0.0 for
Windows-hosted backend services. Tests cover worker routing/failures and service
registry plumbing. Update CI to run gateway tests and affected Django suites.

## Constraints, assumptions and risks
No database/model/schema/migration changes, new registration business logic,
real secret edits, frontend changes or unrelated work. Do not reset Docker,
remove volumes or stop unrelated containers. Gateway Python is infrastructure
routing only; keep it independent of Django/domain modules. Consul is existing
external soa-consul at host.docker.internal:8500 from gateway Docker; host Django
uses localhost:8500. Do not create a competing Consul instance. IPv4/hostname
support is required; valid IPv6 may be supported safely or explicitly documented.
Image build needs network and a Python runtime added to the Nginx Alpine image.
Gateway recreation briefly interrupts incoming traffic. Background process
supervision and config reload failures require tests and clear logs. New service
registration code must be local to each service, never import auth code. Topic's
existing JWT configuration must be preserved, not expanded into unrelated fixes.
