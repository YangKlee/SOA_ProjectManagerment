# Academic Service

Academic Service owns departments, majors, sub-majors, students, and lecturers.
This implementation exposes CRUD APIs for these five resources at port
`8002`. Through the API Gateway, prepend `/academic` to every service path.

## Database boundary

For the current project, academic-service and auth-service use the shared
physical SQLite file `database/DB_ProjectManagerment.db`. This is a project
exception: academic-service owns and accesses only its academic tables; it must
never query or mutate auth-service's `Users` table. SQLite has limited support
for concurrent writers, so production should use separate schemas/credentials
on a server database or separate databases.

## JWT authorization

Set `JWT_SIGNING_KEY` to the exact same secret used by `auth-service`. Do not
commit its real value; use the supplied `.env.example` only as a configuration
template.

Install dependencies using `.\venv\Scripts\python.exe -m pip install -r requirements.txt`.
Settings automatically load this service's `.env` beside `manage.py`, regardless
of the working directory. Existing process environment variables take precedence;
a missing file is allowed. Restart auth and academic servers after editing their
files and log in again. Remove a stale shell key with
`Remove-Item Env:JWT_SIGNING_KEY -ErrorAction SilentlyContinue` before restarting
if you want the file value to take effect. Never commit `.env` or real keys.

Send an access token issued by `auth-service` with every request:

```http
Authorization: Bearer <access-token>
```

For CRUD endpoints, all authenticated roles may use `GET`. `POST`, `PUT`, `PATCH`, and `DELETE`
require the JWT claim `role` to equal the integer `1`.

| Situation | Status |
| --- | ---: |
| Missing, invalid, or expired token | `401` |
| Valid non-role-1 token on a write | `403` |
| Invalid DTO or duplicate field | `400` |
| Unknown resource ID | `404` |

## API endpoints

| Method | Service path | Gateway path | Access |
| --- | --- | --- | --- |
| GET, POST | `/api/departments/` | `/academic/api/departments/` | Read: authenticated; write: role 1 |
| GET, PUT, PATCH, DELETE | `/api/departments/{id}/` | `/academic/api/departments/{id}/` | Read: authenticated; write: role 1 |
| GET, POST | `/api/majors/` | `/academic/api/majors/` | Read: authenticated; write: role 1 |
| GET, PUT, PATCH, DELETE | `/api/majors/{id}/` | `/academic/api/majors/{id}/` | Read: authenticated; write: role 1 |
| GET, POST | `/api/sub-majors/` | `/academic/api/sub-majors/` | Read: authenticated; write: role 1 |
| GET, PUT, PATCH, DELETE | `/api/sub-majors/{id}/` | `/academic/api/sub-majors/{id}/` | Read: authenticated; write: role 1 |
| GET, POST | `/api/students/` | `/academic/api/students/` | Read: authenticated; write: role 1 |
| GET, PUT, PATCH, DELETE | `/api/students/{id}/` | `/academic/api/students/{id}/` | Read: authenticated; write: role 1 |
| GET, POST | `/api/lecturers/` | `/academic/api/lecturers/` | Read: authenticated; write: role 1 |
| GET, PUT, PATCH, DELETE | `/api/lecturers/{id}/` | `/academic/api/lecturers/{id}/` | Read: authenticated; write: role 1 |

## DTOs

All requests and responses use explicit serializers; database models are not
directly serialized.

### Department (`Faculties` table)

Create/update request: `{ "department_id": "F01", "name": "Information Technology" }`

Response: `{ "department_id": "F01", "name": "Information Technology" }`

### Major

Create/update request: `{ "major_id": "KTPM", "name": "Software Engineering", "department_id": "F01" }`

Response includes `major_id`, `name`, and `department_id`.

### Sub-major

Create/update request: `{ "sub_major_id": "WEB", "name": "Web Development", "major_id": "KTPM" }`

Response includes `sub_major_id`, `name`, and `major_id`.

### Student

Create/update request:

```json
{
  "student_id": "SV001",
  "major_id": "KTPM",
  "sub_major_id": "WEB",
  "accumulated_credits": 90,
  "gpa": 3.4
}
```

`sub_major_id` is optional. When present, `sub_major_id` must
belong to the supplied `major_id`.

## Data integrity

### Lecturers (`LectureManager`)

`LectureManager` uses explicit HTTP views, an application service layer, and an
unmanaged model mapping the existing `Lecturers` table. It does not create tables
or require migrations. DTO fields map `lecturer_id` to `LecturerId` and
`department_id` to `FacultyId`. IDs may contain letters, for example `GV001`.

Create request (`POST /api/lecturers/`) and response DTO:

```json
{
  "lecturer_id": "GV001",
  "department_id": "F01"
}
```

`lecturer_id` is required on create and PUT and cannot change on update.
`department_id` is optional and nullable; when supplied, a non-null department
must exist. PATCH preserves omitted fields; `{"department_id": null}` clears the
department. PUT requires `lecturer_id` and preserves an omitted department, in
line with this API's optional-field behavior. No names, email addresses, passwords,
or other auth-owned data are returned. The caller supplies an existing user ID.
This app does not query `Users` or independently verify that ID through an auth
REST contract; the existing database foreign key enforces the reference.

List/retrieve/update return `200`; creation returns `201`; deletion returns `204`
with an empty body. Invalid DTOs, missing departments, duplicate IDs, attempted
ID changes, and database integrity violations return safe field-based `400`
errors. Missing lecturers return `404`. Detail POST returns `405` for authorized
callers. All endpoints require JWT; missing/invalid/expired tokens return `401`,
and authenticated non-role-1 writes return `403`.

Example validation error:

```json
{"department_id": "Department does not exist."}
```

Deletion never cascades into other resources; if the database reports dependent
records, the API returns `400`. Database constraints remain unchanged.

The database hierarchy is `Faculty -> Major -> Specialization`; a Student references a
Major and may reference a SubMajor. Deleting a referenced Department, Major,
or SubMajor is rejected with `400` instead of cascade-deleting academic data.

## Verify

```powershell
cd services\academic-services
..\academic-services\venv\Scripts\python.exe manage.py check
..\academic-services\venv\Scripts\python.exe manage.py test
```


## Gateway service registry integration

The gateway discovers `academic-service` through Consul, rather than a fixed backend URL.
`GET /health/` is public and returns `{"status":"ok","service":"academic-service"}`.
This is a liveness check and does not probe database readiness. JWT authorization
on existing domain endpoints is unchanged.

Settings load this service's `.env` beside `manage.py`; process environment wins.
Install the service's `requirements.txt` in its Python environment. Configure:

```dotenv
CONSUL_AUTO_REGISTER=true
CONSUL_URL=http://localhost:8500
CONSUL_SERVICE_NAME=academic-service
CONSUL_SERVICE_ID=academic-service-8002
CONSUL_SERVICE_ADDRESS=host.docker.internal
CONSUL_SERVICE_PORT=8002
CONSUL_HEALTH_CHECK_URL=http://host.docker.internal:8002/health/
ALLOWED_HOSTS=localhost,127.0.0.1,[::1],host.docker.internal
```

Set `CONSUL_TOKEN` through the environment/file only if registry ACLs require it.
The instance ID must be unique across running instances; change both port and ID
when adding another instance. These address defaults target Django on Windows
and Consul/gateway in Docker Desktop. Use reachable container/service addresses
for a different deployment. Start from this service directory:

```powershell
python manage.py runserver 0.0.0.0:8002
```

Restart after settings/.env changes. Health checks run every 10 seconds with a
2-second timeout and deregister critical instances after one minute. Explicit
commands `python manage.py register_consul` and
`python manage.py register_consul --deregister` update this instance. Admin/test
commands do not register automatically. Keep real secrets out of source control.

Registration runs in a daemon thread without blocking requests. Failed registry
PUTs use 1/2/4/.../30-second backoff, with a 3-second default request timeout.
Successful registrations are refreshed every 30 seconds, recovering from a
registry restart. Set `CONSUL_AUTO_REGISTER=false` (the default) for standalone
commands/development without Consul. No auth-service source imports are used.

## Topic display-name lookup

`POST /api/v1/topic-display-names/` (gateway
`/academic/api/v1/topic-display-names/`) is a read-only batch lookup. All valid
JWT-authenticated readers may call it, including students; it does not apply
CRUD write-role restrictions. The caller JWT is validated locally.

Request and response:

```json
{"major_ids":["1"],"advisor_ids":["GV001"]}
```

```json
{"major_names":{"1":"Information Technology"},"advisor_names":{"GV001":"Nguyen An"}}
```

Both arrays are required and may be empty. Each accepts at most 100 entries,
each a nonblank string <=255 characters; duplicates are removed. The request
must be JSON <=64 KiB, with no unknown fields. ID keys are included even for
missing records, with null values. The batch major lookup accepts TEXT IDs,
including nonnumeric IDs; the existing numeric CRUD detail route is unchanged.
Academic queries only owned Majors/Lecturers and only asks auth about lecturer
IDs that exist in Lecturers, never arbitrary caller-selected user identities.

Configure these environment values (loaded from the service .env, process wins):

```dotenv
# Must match auth-service; use a generated secret, never commit a real value.
DISPLAY_NAMES_SERVICE_TOKEN=
AUTH_NAMES_DISCOVERY_ENABLED=true
AUTH_NAMES_TIMEOUT_SECONDS=2
# Local development only when discovery is explicitly disabled:
AUTH_NAMES_BASE_URL=http://localhost:8001
```

A nonempty matching token in auth and academic is required for lecturer names.
The service resolves healthy auth-service instances through existing CONSUL_*
settings by default. There is no static fallback. With discovery disabled, the
explicit AUTH_NAMES_BASE_URL is used. The token is sent only as X-Service-Token
to auth's `/internal/v1/user-display-names/`; neither the caller JWT nor Consul
ACL token is sent to that endpoint. Secrets and names are excluded from logs.

Each batch performs at most one discovery GET and one read-only auth POST, with
no retries. AUTH_NAMES_TIMEOUT_SECONDS is finite, >0, <=10 (default 2 seconds
per call); responses are limited to 256 KiB and redirects are rejected. No auth
calls are made when there are no existing advisors. A process-local circuit
opens after three failures for ten seconds. An unavailable/misconfigured auth
lookup, timeout, malformed response or upstream HTTP error retains major names
and returns null advisor names. Full names join trimmed LastName then FirstName;
no available name yields null. Names describe current identities, not snapshots.

Statuses: 200 lookup completed (possibly null names); 400 invalid DTO/body;
401 invalid/missing JWT; 415 unsupported content type; 429 rate limit; 503 local
academic storage unavailable. The endpoint has a 120 requests/minute per-user
throttle using Django's configured cache (default local-memory cache is per
process). Auth applies a shared 120/minute service quota. Topic handles these
lookup failures with null-name fallback. No database schema or ownership changes.
Run `python manage.py check` and `python manage.py test`; lookup tests mock HTTP
and ORM boundaries and do not need running auth/Consul.
