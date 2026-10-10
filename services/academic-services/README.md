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

All authenticated roles may use `GET`. `POST`, `PUT`, `PATCH`, and `DELETE`
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
