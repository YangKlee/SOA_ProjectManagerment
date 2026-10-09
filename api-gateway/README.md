# API Gateway

Nginx API Gateway listens on `http://localhost:8000` and routes public requests
to the independent Django services.

| Gateway URL | Target service |
| --- | --- |
| `/auth/*` | `http://localhost:8001/*` — auth-service |
| `/academic/*` | `http://localhost:8002/*` — academic-service |
| `/registrations/*` | `http://localhost:8003/*` — regist-service |
| `/topics/*` | `http://localhost:8004/*` — topic-service |

The gateway forwards `Authorization: Bearer <JWT>` to each target. Services
validate JWT signature and expiry locally; the gateway does not own domain
models or business logic.

## Run

Start the backend services on ports 8001–8004, then run:

```powershell
cd api-gateway
docker compose up -d
```

Useful public routes include:

```text
POST /auth/login/
GET  /academic/api/students/
GET  /topics/api/topics/
GET  /registrations/
```

Stop the gateway with `docker compose down`.
