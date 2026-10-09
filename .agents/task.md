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
