# Academic Service

Academic Service owns departments, majors, sub-majors, students, and topics.
This implementation exposes CRUD APIs for the first four resources at port
`8002`. Through the API Gateway, prepend `/academic` to every service path.

## JWT authorization

Set `JWT_SIGNING_KEY` to the exact same secret used by `auth-service`. Do not
commit its real value; use the supplied `.env.example` only as a configuration
template.

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

## DTOs

All requests and responses use explicit serializers; database models are not
directly serialized.

### Department

Create/update request: `{ "code": "CNTT", "name": "Information Technology" }`

Response: `{ "id": 1, "code": "CNTT", "name": "Information Technology" }`

### Major

Create/update request: `{ "code": "KTPM", "name": "Software Engineering", "department_id": 1 }`

Response includes `id`, `code`, `name`, and `department_id`.

### Sub-major

Create/update request: `{ "code": "WEB", "name": "Web Development", "major_id": 1 }`

Response includes `id`, `code`, `name`, and `major_id`.

### Student

Create/update request:

```json
{
  "student_code": "SV001",
  "full_name": "Nguyen An",
  "email": "an@example.com",
  "phone": "0900000000",
  "major_id": 1,
  "sub_major_id": 1
}
```

`phone` and `sub_major_id` are optional. When present, `sub_major_id` must
belong to the supplied `major_id`.

## Data integrity

The hierarchy is `Department -> Major -> SubMajor`; a Student references a
Major and may reference a SubMajor. Deleting a referenced Department, Major,
or SubMajor is rejected with `400` instead of cascade-deleting academic data.

## Verify

```powershell
cd services\academic-services
..\academic-services\venv\Scripts\python.exe manage.py check
..\academic-services\venv\Scripts\python.exe manage.py test
```
