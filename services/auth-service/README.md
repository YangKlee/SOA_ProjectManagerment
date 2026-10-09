# Auth Service

## Consul service registration

The service exposes `GET /health/`.  When `CONSUL_AUTO_REGISTER=true`, it
registers itself after Django starts. Consul then checks that endpoint every
10 seconds and removes the instance after one minute of failed checks.

Start a local Consul development agent:

```powershell
docker run --rm --name soa-consul -p 8500:8500 hashicorp/consul agent -dev -client=0.0.0.0
```

In another PowerShell window, start the auth service with registration
enabled. This configuration is for Django running on Windows while Consul is
inside Docker:

```powershell
$env:CONSUL_AUTO_REGISTER = "true"
$env:CONSUL_SERVICE_ADDRESS = "host.docker.internal"
$env:CONSUL_HEALTH_CHECK_URL = "http://host.docker.internal:8000/health/"
python manage.py runserver 8000
```

Open `http://localhost:8500` and verify the healthy `auth-service` entry.

For a one-off registration, without enabling startup registration:

```powershell
python manage.py register_consul
python manage.py register_consul --deregister
```

All configuration keys and defaults are listed in `.env.example`. The project
does not load `.env` files automatically; set those values through the shell,
Docker Compose environment, or your deployment platform.
