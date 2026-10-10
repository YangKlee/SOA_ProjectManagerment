# Task: Configure Gateway CORS for the frontend origin

## Objective
Fix browser login CORS at the API Gateway while retaining frontend `VITE_API_BASE_URL=http://localhost:8000`, service ports, routes, discovery and JWT forwarding.

## Status
User selected Gateway CORS instead of the earlier development-proxy proposal. Awaiting approval of this revised implementation plan. No proxy/frontend environment edits have been made.

## Evidence
- Frontend `.env` points directly to Gateway port 8000; Vite serves port 5173.
- Gateway README explicitly states CORS is not implemented.
- Gateway discovery.py dynamically generates Nginx config at bootstrap and every route update. Editing only nginx.conf would be overwritten.

## Scope
- Add configurable `CORS_ALLOWED_ORIGINS`, comma-separated exact HTTP(S) origins. Local defaults: `http://localhost:5173,http://127.0.0.1:5173`. Explicit empty configuration disables cross-origin access; reject wildcard/malformed/injectable values before generating Nginx directives.
- Apply CORS in generated Nginx configs and align the checked-in bootstrap config.
- Answer OPTIONS preflight locally for existing Gateway API prefixes without requiring healthy upstreams; allow GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS and request headers Authorization, Content-Type, Accept, X-Request-ID.
- Reflect only an allowlisted origin, emit Vary: Origin, and preserve CORS headers on actual success, validation/auth errors and Gateway failures. Do not enable cookie credentials or wildcard origins.
- Prevent duplicate/conflicting upstream CORS headers. Preserve Authorization forwarding, request body, routes, health/discovery, timeout and no-write-retry behavior.
- Wire CORS environment setting through Compose and .env.example; preserve existing local Gateway .env entries if an origin override needs updating.
- Add unit tests and real-Nginx integration tests using isolated mock registry/backends.
- Update Gateway README, root README and frontend README for CORS configuration, preflight and deployment/restart instructions.
- If Docker is available, build/test an isolated Gateway image, then recreate only the Gateway container with the updated image/config so the fix takes effect. Do not start/recreate Consul or Django services.

## Constraints
- Before revised-plan approval, write only fe/.agents/task.md and fe/.agents/plan.md.
- No frontend proxy or API URL change. No database, Django source, migrations, dependency locks or unrelated configuration edits.
- No browser-security bypass or wildcard CORS. Backend authorization remains in the owning services.
- Preserve all unrelated user edits and environment values; do not print secrets or submit real login credentials.
- Infrastructure changes are limited to Gateway config/generator/Compose/tests documented here. CI updates only if existing Gateway check commands require changes.

## Acceptance criteria
- Allowed origins receive exact Access-Control-Allow-Origin and Vary: Origin on preflight and actual responses including 400/401/403/503.
- Allowed OPTIONS /auth/login/ with Content-Type and Authorization returns successful preflight without forwarding to auth-service; disallowed origins receive no allowing origin header.
- Configuration rejects wildcard and directive injection, supports explicit empty allowlist, and persists across discovery reloads.
- Existing route/query/body/Bearer forwarding and resilience tests pass.
- Gateway unit tests and available Nginx integration checks pass. Existing frontend lint/test/build remain passing.
- Where runtime access is available, live Gateway preflight from both local frontend origins verifies the deployed fix; login with a real account is not claimed without testing.

## Assumptions and risks
- Frontend normally opens on localhost:5173 or 127.0.0.1:5173. Other origins must be added explicitly through the allowlist.
- CORS enables browser access but does not repair unavailable Consul/upstreams, bad credentials or unrelated network failures.
- Recreating Gateway causes a brief Gateway interruption. Backend services and data are not modified.
- Docker/Nginx may be unavailable; report exact verification and deployment limitations instead of claiming runtime success.
