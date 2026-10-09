# Coding Agent Guide

This repository is a Service-Oriented Architecture (SOA) graduation-project
management system. Follow this guide for every task in this repository.

## Mandatory task workflow

Before performing any implementation, configuration, dependency, database,
infrastructure, or documentation change:

1. Create or update `.agents/task.md` with the task objective, scope,
   constraints, acceptance criteria, assumptions, and risks.
2. Create or update `.agents/plan.md` with the ordered implementation steps,
   files expected to change, verification steps, and rollback notes.
3. Present the task and plan to the user and ask for explicit confirmation.
4. Stop and wait for an explicit approval such as `approve`, `approved`, or
   `go ahead`.
5. Only after approval, perform the planned work. If scope changes materially,
   update both files and request confirmation again.

The only allowed writes before confirmation are `.agents/task.md` and
`.agents/plan.md`. Do not edit source code, run migrations, install packages,
start containers, call external services, or modify configuration before the
user confirms the plan. Do not treat silence as approval.

For read-only questions, provide an evidence-based answer without changing
files. If inspection is needed, state that it is read-only and keep it scoped.

## Product goal

Build a graduation-project management system for students. The system must use
SOA: independent services collaborate and exchange data through standard
HTTP/REST interfaces. The minimum academic domain is:

- `SINHVIEN` / `Students`
- `DETAI` / `Topics`
- `DANGKY` / `Registrations`

The implementation must visibly demonstrate independent services, standardized
communication, and service reusability.

## Required architecture

```text
                         +------------------+
                         |  Consul :8500    |
                         | Service Registry |
                         +--------+---------+
                                  ^
                                  | registration / discovery
                                  |
Client ---> API Gateway :8000 ----+------------------------------+
             |                   |                              |
             v                   v                              v
     auth-service :8001  academic-service :8002  regist-service :8003
             |                   |                              |
             |                   |<---- REST validation ---------+
             v                   v                              v
          Users             Students, Topics                Registrations
```

### Fixed ports and routes

| Component | Port | Gateway route |
| --- | ---: | --- |
| API Gateway | `8000` | Public entry point |
| auth-service | `8001` | `/auth/*` |
| academic-service | `8002` | `/academic/*` |
| regist-service | `8003` | `/registrations/*` |
| Consul | `8500` | Registry UI/API |

Do not change these ports, service names, or gateway prefixes without an
explicit user-approved plan and corresponding updates to configuration,
documentation, tests, and CI.

### Service boundaries and ownership

- **auth-service** owns identity and authentication: `Users`, passwords, JWT,
  login, refresh tokens, and the current-user profile.
- **academic-service** owns academic data: students, lecturers, faculties,
  majors, specializations, and topics.
- **regist-service** owns registrations and registration business rules.
- **log-service** owns audit/log records. It must not become a dependency that
  blocks the main request path.
- **api-gateway** only routes, enforces cross-cutting policy, and forwards
  headers. It must not contain domain models or business logic.
- **Consul** is the service registry. It is not an API Gateway and not an ESB.

Each service owns its code and its data boundary. A service must never import
another service's Django model, access another service's ORM, or directly query
another service's database. Cross-service references are IDs and are validated
through HTTP/REST contracts.

## SOA principles to enforce

### Loose coupling

- Depend only on another service's published contract, not its source code,
  internal database schema, private URL structure, or implementation details.
- Use versioned REST endpoints, JSON DTOs/serializers, documented status codes,
  and stable error responses.
- Use service discovery when dynamic endpoints are required. Do not hard-code
  an inter-service address when Consul discovery is enabled.

### Service reusability

- Design services around reusable business capabilities, not one UI screen or
  one caller.
- Keep authentication, academic data, and registration rules centralized in
  their owning services. Do not duplicate those rules in callers.
- Version breaking API changes and preserve compatible DTO fields whenever
  possible.

### Asynchronous communication

- Keep synchronous REST calls for request/response operations that need an
  immediate answer, such as validating a topic before registration.
- Use asynchronous events for non-blocking work such as audit logging,
  notifications, analytics, and retryable background processing.
- Before adding a broker or queue, document the event contract, producer,
  consumer, retry policy, idempotency key, ordering assumption, and dead-letter
  behavior in the task and plan.
- Never retry non-idempotent write requests blindly.

### Policy management

- Authenticate public protected endpoints with JWT. auth-service issues tokens;
  consuming services validate token signature, expiration, and authorization.
- Apply authorization by role and ownership, not only by a client-supplied ID.
- API Gateway may enforce CORS, TLS termination, rate limiting, request size,
  and coarse-grained authentication. Services must still validate authorization.
- Keep secrets, JWT signing keys, Consul tokens, and credentials in environment
  variables or secret stores. Never commit them to source control.
- Log security-relevant operations with correlation/request IDs while excluding
  passwords, tokens, and sensitive personal data.
- Define timeouts, expected response behavior, and rate limits for every new
  inter-service contract.

### Interoperability

- Use HTTP/REST, JSON, UTF-8, ISO-8601 date/time values, and documented HTTP
  status codes.
- Use explicit request and response DTOs (Django REST Framework serializers).
  Never serialize a database model directly when it can reveal private fields.
- Document endpoints, request/response examples, authentication, errors, and
  caller expectations in the relevant service README or OpenAPI document.

### Automatic discovery and dynamic binding

- Expose `GET /health/` for every service.
- Register each running instance with Consul using a unique instance ID, service
  name, address, port, and HTTP health check.
- Resolve healthy instances by service name through Consul for runtime service
  discovery. Configure bounded timeouts and a safe failure response.
- Treat static local URLs as development configuration only; do not make them a
  hidden dependency in production-oriented service clients.

### Self-healing and resilience

- Configure health checks and deregistration of unhealthy instances.
- Use short timeouts, bounded retries with backoff only for safe/idempotent
  requests, and circuit-breaker/fallback behavior for critical dependencies.
- Make write operations idempotent where practical, especially registration and
  message consumers.
- Return clear, safe `4xx` and `5xx` responses; do not expose stack traces or
  internal service credentials.

## API and security rules

- Preserve the current public auth contract unless a user-approved task changes
  it: `GET /health/`, `POST /login/`, `POST /token/refresh/`, and `GET /me/`.
- Forward `Authorization: Bearer <token>` through the API Gateway.
- Do not query the auth database from academic or registration services.
- Do not call auth-service for every protected request. Validate JWT locally;
  call auth-service only when current identity data or revocation/state is
  genuinely required.
- An internal endpoint for querying an arbitrary user must use service-to-service
  authentication and must not be publicly exposed without authorization.

## Coding, testing, and verification

- Every code change must include automated tests in the same task. A change is
  incomplete until relevant tests are added or updated.
- Test success paths, validation failures, authorization failures, and relevant
  service-client failure behavior.
- Run the smallest relevant tests during development and the affected Django
  checks before handoff. At minimum, run:

  ```powershell
  python manage.py check
  python manage.py test
  ```

- Keep GitHub Actions at `.github/workflows/python-tests.yml` passing. Update
  CI whenever service dependencies or test commands change.
- Do not modify generated database files, migrations, dependency locks, or
  infrastructure files unless they are explicitly in the approved plan.

## Documentation and delivery

- Update the root README and the affected service README when ports, routes,
  API contracts, environment variables, architecture, or run instructions
  change.
- In the final response, summarize changed files, API/architecture impact,
  verification performed, and any remaining limitations.
- Be precise about implementation status. Do not claim a service, route,
  integration, resilience mechanism, or policy exists unless it is implemented
  and verified.
