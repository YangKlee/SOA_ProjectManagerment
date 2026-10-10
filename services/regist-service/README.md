# Registration Service

This service currently has no registration business API implemented.


## Gateway service registry integration

The gateway discovers `regist-service` through Consul, rather than a fixed backend URL.
`GET /health/` is public and returns `{"status":"ok","service":"regist-service"}`.
This is a liveness check and does not probe database readiness. JWT authorization
on existing domain endpoints is unchanged.

Settings load this service's `.env` beside `manage.py`; process environment wins.
Install the service's `requirements.txt` in its Python environment. Configure:

```dotenv
CONSUL_AUTO_REGISTER=true
CONSUL_URL=http://localhost:8500
CONSUL_SERVICE_NAME=regist-service
CONSUL_SERVICE_ID=regist-service-8003
CONSUL_SERVICE_ADDRESS=host.docker.internal
CONSUL_SERVICE_PORT=8003
CONSUL_HEALTH_CHECK_URL=http://host.docker.internal:8003/health/
ALLOWED_HOSTS=localhost,127.0.0.1,[::1],host.docker.internal
```

Set `CONSUL_TOKEN` through the environment/file only if registry ACLs require it.
The instance ID must be unique across running instances; change both port and ID
when adding another instance. These address defaults target Django on Windows
and Consul/gateway in Docker Desktop. Use reachable container/service addresses
for a different deployment. Start from this service directory:

```powershell
python manage.py runserver 0.0.0.0:8003
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
