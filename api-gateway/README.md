# API Gateway with Consul discovery

Nginx listens on port `8000`. A Python standard-library worker queries Consul
`GET /v1/health/service/{name}?passing=true`, validates addresses/ports and renders
Nginx upstreams from healthy instances. Backend addresses are not fixed in the
image. Service addresses fall back to the Consul node address only when the
registered service address is empty. IPv4, IPv6 and DNS hostnames are supported.

| Gateway prefix | Consul service name | Prefix forwarded |
| --- | --- | --- |
| `/auth/` | `auth-service` | `/` |
| `/academic/` | `academic-service` | `/` |
| `/registrations/` | `regist-service` | `/` |
| `/topics/` | `topic-service` | `/` |

For example, `/academic/api/lecturers/?page=2` becomes `/api/lecturers/?page=2`.
Authorization and forwarding headers are preserved; a gateway-generated
`X-Request-ID` is forwarded. Services remain responsible for JWT and role checks.
Gateway code contains no domain models or business rules. Access logs exclude
Authorization, request bodies and query strings. CORS is not implemented here.

## Run on Windows with Docker Desktop

1. Start Docker Desktop and the existing Consul container at port `8500`.
2. Configure each backend's `.env` using its `.env.example`. Set
   `CONSUL_AUTO_REGISTER=true`; use a unique `CONSUL_SERVICE_ID` per instance.
   Keep the same JWT signing key for auth, academic and topic.
3. Run each Django server on its assigned port, bound to `0.0.0.0`, for example:

```powershell
cd services\academic-services
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8002
```

Use ports 8001/8003/8004 in auth/regist/topic respectively. Regist currently uses
an available project Python environment if it has no service-local venv.
`ALLOWED_HOSTS` must include `host.docker.internal` and the host sent by clients.
The local defaults include localhost, loopback and host.docker.internal.

4. Open http://localhost:8500 and confirm the instances are Passing. Only healthy
   registered instances can receive gateway traffic. After starting a service,
   allow a health-check interval (10 seconds). Existing auth registration can be
   retriggered using `python manage.py register_consul` if necessary.
5. From `api-gateway`, optionally copy `.env.example` to `.env` and build/start:

```powershell
docker compose up -d --build
docker compose ps
docker compose logs --tail 30
docker compose exec -T api-gateway nginx -t
```

Compose reads its own `.env`. Inside the gateway container, Consul's URL is
`http://host.docker.internal:8500`; backend Django uses `http://localhost:8500`
when running on Windows. Do not use container-local localhost for a host registry.
This setup reuses the existing Consul instance; Compose does not start another.

## Configuration and failures

| Variable | Default | Meaning |
| --- | --- | --- |
| `CONSUL_URL` | `http://host.docker.internal:8500` | Registry HTTP(S) endpoint |
| `CONSUL_TOKEN` | empty | Optional ACL token, never logged |
| `CONSUL_REFRESH_SECONDS` | `3` | Refresh interval after each polling cycle |
| `CONSUL_TIMEOUT_SECONDS` | `2` | Per-registry-request socket timeout |
| `CONSUL_STALE_TTL_SECONDS` | `15` | Maximum age for cached discovery data |

The four services are queried concurrently. Startup works without Consul and
returns JSON `503` for unavailable service routes. A successful empty lookup
removes its upstream immediately. On lookup failure, last good instances are
used only while younger than the stale TTL. Expiration takes effect on the next
poll; detection includes the poll interval and lookup timeout. This is bounded
polling, not immediate health push. Unknown paths return JSON `404`.

Multiple healthy instances use Nginx round-robin balancing. Candidate configs are
checked with `nginx -t`; only changed, valid configs are replaced and reloaded.
A failed config validation/reload terminates the supervised process/container
instead of indefinitely keeping stale routes; Compose restarts it with a safe
bootstrap. Nginx gets graceful shutdown (up to 12 seconds) before forceful exit.
Worker and Nginx are supervised together; an unexpected Nginx exit also ends the
container. In-flight requests may finish during a normal reload.

Proxy connect timeout is 2 seconds; read/send inactivity timeouts are 10 seconds.
Automatic upstream retries are disabled for all methods, including writes.
Connection/timeout errors return a safe JSON `503`. A live backend can still
return application `4xx` responses; registration does not implement domain APIs.
In particular, regist-service currently has health/registry plumbing but no
registration business API. Services keep their own data ownership.

## Verification

```powershell
python -m unittest discover -s tests -p 'test_*.py'
docker compose config --quiet
docker compose build
docker run --rm --mount "type=bind,source=$($PWD.Path)\tests,target=/tests,readonly" --entrypoint python3 soa-api-gateway:local /tests/integration.py
```

Integration tests run mock registry/backends inside a disposable container,
without contacting the real Consul, Django servers or project database. They
exercise actual Nginx reloads, changing instance ports, balancing, JWT/header and
query forwarding, unavailable services, registry outage/recovery and no write
replay. CI runs these checks in `.github/workflows/python-tests.yml`.

Use `docker compose stop` to stop this gateway only. No volume or database
cleanup is required. Production Consul deployment must supply its own security,
durable state and routing/host configuration; the local Consul dev container is
not a production cluster.

References: [Consul health service API](https://developer.hashicorp.com/consul/api-docs/health),
[Nginx proxy retry policy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_next_upstream).
