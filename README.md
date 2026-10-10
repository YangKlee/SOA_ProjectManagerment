# Graduation Project Management System — SOA

## React frontend

The frontend in `fe/` uses React, Vite, TypeScript, and a shared Axios client.
Use Node.js 24 and npm:

```powershell
cd fe
npm ci
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`. `VITE_API_BASE_URL` configures the public Gateway
URL (development default: `http://localhost:8000`). In production, set it before
building, or serve the frontend and Gateway routes on the same origin. Never put
secrets in `VITE_*` variables. Cross-origin requests require Gateway CORS support.

Run `npm run lint`, `npm run test`, and `npm run build` inside `fe/`.
Frontend checks run independently in `.github/workflows/frontend-tests.yml`.
Login calls `/auth/login/` using MSSV/UserID and password. Server role 1 routes
to `/admin`, role 2 to `/lecture`, and role 3 to `/student`. Role routes require
an in-memory session and support logout; their domain screens are placeholders.
Reload requires login again. Frontend auth tests use mocked API responses;
live Gateway/account integration has not been verified. Production hosting
needs SPA history fallback while preserving API forwarding.
See [frontend README](fe/README.md)
for structure, error handling, and client usage. Backend ports and routes remain unchanged.

Hệ thống quản lý đồ án tốt nghiệp theo kiến trúc SOA. Mỗi service là một Django
project độc lập, giao tiếp bằng HTTP/REST và JSON.

## Architecture

```text
Client -> API Gateway :8000
           ├─ /auth/*          -> auth-service :8001
           ├─ /academic/*      -> academic-service :8002
           ├─ /registrations/* -> regist-service :8003
           └─ /topics/*        -> topic-service :8004

Consul :8500 provides service discovery.
```

| Service | Port | Ownership |
| --- | ---: | --- |
| auth-service | 8001 | `Users`, passwords, JWT, current profile |
| academic-service | 8002 | `Faculties`, `Majors`, `Specializations`, `Students`, `Lecturers` |
| regist-service | 8003 | `Registrations` and registration rules |
| topic-service | 8004 | `Topics` and topic lifecycle |
| log-service | — | `AuditLogs` without blocking request paths |
| API Gateway | 8000 | Routing and cross-cutting policy |
| Consul | 8500 | Service registry/discovery |

## Shared database and database-first

Services share the physical SQLite file `database/DB_ProjectManagerment.db`.
This does not share data ownership: a service accesses only the tables it owns,
does not import another service's models, and uses IDs/REST contracts across
boundaries.

The database schema is the source of truth. Django mappings use explicit
`db_table`/`db_column` values with `Meta.managed = False`; schema-altering
migrations require an approved task, backup, and rollback plan.

## Gateway routes

| Prefix | Target |
| --- | --- |
| `/auth/*` | auth-service :8001 |
| `/academic/*` | academic-service :8002 |
| `/registrations/*` | regist-service :8003 |
| `/topics/*` | topic-service :8004 |

The gateway forwards `Authorization: Bearer <token>`. Services validate JWTs
locally with the shared `JWT_SIGNING_KEY` environment value. Authenticated roles
may read academic/topic data; writes require JWT claim `role: 1`.

Auth-service login compares passwords directly with plaintext `Users.Password`
values; no password hash verification or database conversion is performed.
This project policy is unsuitable for production because database access exposes
stored passwords. JWT signing and validation remain enabled. See the
[auth-service README](services/auth-service/README.md) for the login contract.

## Repository layout

Academic-service includes `LectureManager` for lecturer CRUD. Its gateway routes
are `/academic/api/lecturers/` (GET/POST) and
`/academic/api/lecturers/{id}/` (GET/PUT/PATCH/DELETE), with string IDs such as
`GV001`. Send a bearer access token: every authenticated role may read, and role
`1` is required to write. DTOs contain `lecturer_id` and nullable `department_id`;
identity data remains owned by auth-service. The app maps the existing Lecturers
table without schema migrations. See the [academic-service README](services/academic-services/README.md)
for examples, status codes and the existing-user-ID requirement.

```text
services/
  auth-service/
  academic-services/
  topic-service/       # topic_manager app
  regist-service/
  log-services/
database/DB_ProjectManagerment.db
api-gateway/
```

## Run services

Use each service's own virtual environment and configure the same
`JWT_SIGNING_KEY` for auth, academic, and topic services.

Auth and academic services automatically load their own `.env` beside `manage.py`
using `python-dotenv`. Install each service's `requirements.txt` in its venv.
Set the same `JWT_SIGNING_KEY` in `services/auth-service/.env` and
`services/academic-services/.env`; process environment values take precedence.
Restart both servers after edits and log in again for a new access token. Missing
files are allowed for deployments that supply environment variables. Other
services still require their existing environment setup. Do not commit secrets.

```powershell
cd services\auth-service; .\venv\Scripts\python.exe manage.py runserver 8001
cd services\academic-services; .\venv\Scripts\python.exe manage.py runserver 8002
cd services\topic-service; .\venv\Scripts\python.exe manage.py runserver 8004
cd services\regist-service; .\venv\Scripts\python.exe manage.py runserver 8003
```

Topic Service exposes `GET /health/`, `GET /api/topics/`, and protected topic
write endpoints. See [topic-service README](services/topic-service/README.md)
for details.
