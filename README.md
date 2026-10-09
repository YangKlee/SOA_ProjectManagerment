# Graduation Project Management System — SOA

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

## Repository layout

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

```powershell
cd services\auth-service; .\venv\Scripts\python.exe manage.py runserver 8001
cd services\academic-services; .\venv\Scripts\python.exe manage.py runserver 8002
cd services\topic-service; .\venv\Scripts\python.exe manage.py runserver 8004
cd services\regist-service; .\venv\Scripts\python.exe manage.py runserver 8003
```

Topic Service exposes `GET /health/`, `GET /api/topics/`, and protected topic
write endpoints. See [topic-service README](services/topic-service/README.md)
for details.
