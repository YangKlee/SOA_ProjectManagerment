# Auth Service

`auth-service` is the identity provider for the graduation-project management
system. It authenticates records in the existing `Users` table, issues JWTs,
and exposes the authenticated user's safe profile. It does not return a
password in any response.

## Responsibilities

- Authenticate with email or user ID and password.
- Issue and refresh JWT access tokens.
- Return the current authenticated user's profile.
- Register itself in Consul when service discovery is enabled.

The service owns authentication concerns. Other services must not import the
`Users` model or query the auth database directly; they receive a JWT from the
client and validate it, or call auth-service through REST when necessary.

## Run locally

From this directory:

```powershell
..\..\venv\Scripts\python.exe -m pip install -r requirements.txt
..\..\venv\Scripts\python.exe manage.py runserver 8001
```

The direct base URL is `http://localhost:8001`.

When the API Gateway is running, use `http://localhost:8000/auth` instead.
For example, gateway URL `/auth/login/` is forwarded to this service's
`/login/` endpoint.

## API contract

| Method | Service URL | Gateway URL | Authentication | Purpose |
| --- | --- | --- | --- | --- |
| `GET` | `/health/` | `/auth/health/` | None | Liveness check |
| `POST` | `/login/` | `/auth/login/` | None | Log in and issue tokens |
| `POST` | `/token/refresh/` | `/auth/token/refresh/` | None | Create a new access token |
| `GET` | `/me/` | `/auth/me/` | Bearer access token | Get current user profile |

### `POST /login/`

Request DTO: provide one of `identifier`, `email`, or `userid`, together with
`password`.

```json
{
  "identifier": "sv001@example.com",
  "password": "your-password"
}
```

Successful response (`200 OK`):

```json
{
  "access": "<JWT access token>",
  "refresh": "<JWT refresh token>",
  "token_type": "Bearer",
  "user": {
    "user_id": "SV001",
    "first_name": "An",
    "last_name": "Nguyen",
    "gender": 1,
    "date_of_birth": "2003-01-15",
    "email": "sv001@example.com",
    "phone": "0900000000",
    "role": 1,
    "status": 1,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  }
}
```

Invalid credentials return `401 Unauthorized`. Invalid or missing fields
return `400 Bad Request`.

Login compares the supplied password exactly with the plaintext value in
`Users.Password`, including whitespace and Unicode. It does not verify password
hashes or convert stored values. Accounts containing hashes cannot authenticate
with their original passwords under this policy. Plaintext password storage is
for this project only and is unsuitable for production: database readers can
read every stored password. JWT signing and bearer authentication are unchanged.

### `POST /token/refresh/`

Request DTO:

```json
{
  "refresh": "<JWT refresh token>"
}
```

Successful response:

```json
{
  "access": "<new JWT access token>",
  "token_type": "Bearer"
}
```

### `GET /me/`

Send the access token:

```http
Authorization: Bearer <JWT access token>
```

The response is the `user` DTO shown in the login response. The `password`
column is never serialized.

## JWT and other services

The login token includes `user_id`, `email`, and `role` claims. Academic and
registration services should validate its signature and expiration locally,
then use those claims for authorization. They should not call `/me/` for every
request.

For the current Django setup, configure the same explicit JWT signing key (or
preferably an auth-service private key and a public key in consuming services)
before sharing tokens across services. Do not rely on each service's separate
Django `SECRET_KEY` and do not commit the signing key to Git.

## Consul service registration

The service has a public `GET /health/` endpoint. When
`CONSUL_AUTO_REGISTER=true`, it registers an `auth-service` instance at
startup. Consul checks the health endpoint every 10 seconds and deregisters an
instance after one minute of failed checks.

Start a local Consul development agent:

```powershell
docker run --rm --name soa-consul -p 8500:8500 hashicorp/consul agent -dev -client=0.0.0.0
```

In another PowerShell window, enable registration and run auth-service. The
following address is correct when Django runs on Windows and Consul runs in a
Docker container:

```powershell
$env:CONSUL_AUTO_REGISTER = "true"
$env:CONSUL_SERVICE_ADDRESS = "host.docker.internal"
$env:CONSUL_HEALTH_CHECK_URL = "http://host.docker.internal:8001/health/"
..\..\venv\Scripts\python.exe manage.py runserver 8001
```

Open `http://localhost:8500` and verify that `auth-service` is healthy.

For a one-off operation:

```powershell
..\..\venv\Scripts\python.exe manage.py register_consul
..\..\venv\Scripts\python.exe manage.py register_consul --deregister
```

Configuration keys and defaults are in [.env.example](.env.example). Install
dependencies with `.\venv\Scripts\python.exe -m pip install -r requirements.txt`.
Settings automatically load `.env` beside this service's `manage.py`, regardless
of the working directory, before reading JWT and Consul configuration. Existing
process environment variables take precedence over file values. A missing file
is allowed; do not commit real secrets. Use the same `JWT_SIGNING_KEY` in auth
and academic services. Restart both servers after changing `.env`, then log in
again to get a token signed with the current key. If an old shell value remains,
remove it with `Remove-Item Env:JWT_SIGNING_KEY -ErrorAction SilentlyContinue`
before restarting. `CONSUL_AUTO_REGISTER=true` in `.env` enables registration
on startup and requires the configured Consul instance to be available.

## Verification

```powershell
..\..\venv\Scripts\python.exe manage.py check
..\..\venv\Scripts\python.exe manage.py test authentication
```


## Gateway service registry integration

The gateway discovers `auth-service` through Consul, rather than a fixed backend URL.
`GET /health/` is public and returns `{"status":"ok","service":"auth-service"}`.
This is a liveness check and does not probe database readiness. JWT authorization
on existing domain endpoints is unchanged.

Settings load this service's `.env` beside `manage.py`; process environment wins.
Install the service's `requirements.txt` in its Python environment. Configure:

```dotenv
CONSUL_AUTO_REGISTER=true
CONSUL_URL=http://localhost:8500
CONSUL_SERVICE_NAME=auth-service
CONSUL_SERVICE_ID=auth-service-8001
CONSUL_SERVICE_ADDRESS=host.docker.internal
CONSUL_SERVICE_PORT=8001
CONSUL_HEALTH_CHECK_URL=http://host.docker.internal:8001/health/
ALLOWED_HOSTS=localhost,127.0.0.1,[::1],host.docker.internal
```

Set `CONSUL_TOKEN` through the environment/file only if registry ACLs require it.
The instance ID must be unique across running instances; change both port and ID
when adding another instance. These address defaults target Django on Windows
and Consul/gateway in Docker Desktop. Use reachable container/service addresses
for a different deployment. Start from this service directory:

```powershell
python manage.py runserver 0.0.0.0:8001
```

Restart after settings/.env changes. Health checks run every 10 seconds with a
2-second timeout and deregister critical instances after one minute. Explicit
commands `python manage.py register_consul` and
`python manage.py register_consul --deregister` update this instance. Admin/test
commands do not register automatically. Keep real secrets out of source control.

Existing auth automatic registration makes a background attempt at startup;
it does not have periodic retry. If Consul was unavailable or restarted, run
`python manage.py register_consul` again after it is available.
