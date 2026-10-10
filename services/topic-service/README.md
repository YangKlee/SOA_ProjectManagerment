# Topic Service

`topic-service` owns the existing `Topics` table in the shared project
database. It uses database-first mapping (`managed = False`) and never creates
or migrates that schema.

Run on port `8004` after setting the same `JWT_SIGNING_KEY` as auth-service.

- `GET /health/` is public.
- `GET /api/topics/` requires a valid JWT.
- Topic writes require JWT `role: 1`.


## Gateway service registry integration

The gateway discovers `topic-service` through Consul, rather than a fixed backend URL.
`GET /health/` is public and returns `{"status":"ok","service":"topic-service"}`.
This is a liveness check and does not probe database readiness. JWT authorization
on existing domain endpoints is unchanged.

Settings load this service's `.env` beside `manage.py`; process environment wins.
Install the service's `requirements.txt` in its Python environment. Configure:

```dotenv
CONSUL_AUTO_REGISTER=true
CONSUL_URL=http://localhost:8500
CONSUL_SERVICE_NAME=topic-service
CONSUL_SERVICE_ID=topic-service-8004
CONSUL_SERVICE_ADDRESS=host.docker.internal
CONSUL_SERVICE_PORT=8004
CONSUL_HEALTH_CHECK_URL=http://host.docker.internal:8004/health/
ALLOWED_HOSTS=localhost,127.0.0.1,[::1],host.docker.internal
```

Set `CONSUL_TOKEN` through the environment/file only if registry ACLs require it.
The instance ID must be unique across running instances; change both port and ID
when adding another instance. These address defaults target Django on Windows
and Consul/gateway in Docker Desktop. Use reachable container/service addresses
for a different deployment. Start from this service directory:

```powershell
python manage.py runserver 0.0.0.0:8004
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
