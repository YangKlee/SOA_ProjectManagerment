# Task: Use Vite proxy for local API requests

## Objective
Use same-origin Axios base URL `/` and Vite development proxy to the existing API Gateway at http://localhost:8000, as newly selected by the user.

## Status
Completed after user approval (`ok`). Vite proxy, same-origin Axios base and local `.env` are configured. CORS additions selectively reverted, preserving discovery; integration.py was already restored when work resumed and was left untouched. Gateway local image rebuilt from restored source; running container unchanged. All 65 frontend tests, lint/build, 9 Gateway tests and Compose validation passed. The existing Vite server serves the updated same-origin API configuration. No real account login tested.

## Scope
- Selectively undo only Gateway CORS changes introduced by this agent: origin parsing/maps/preflight/headers, Compose CORS variable, example environment CORS entries and added CORS tests. Preserve pre-existing discovery, routes, tests and all other user edits, even if changes have since been committed.
- Restore local soa-api-gateway:local to non-CORS source. Since Docker cannot tag the old container image ID directly, rebuild restored source for the local image tag; do not restart/recreate containers or remove images.
- Configure Vite development proxy for existing Gateway prefixes `/auth`, `/academic`, `/registrations`, `/topics`; preserve method, URL, body and Authorization.
- Default Axios API base to `/`; update only VITE_API_BASE_URL in fe/.env and fe/.env.example to `/`. Preserve all unrelated environment entries.
- Add optional public VITE_API_PROXY_TARGET, default http://localhost:8000, for the development proxy target.
- Add automated proxy integration tests using ephemeral local mock Gateway and Vite server; keep login/role tests passing.
- Update frontend README and root README frontend section with local request flow, required Vite restart and production configuration.

## Constraints
- Until revised approval, write only fe/.agents/task.md and fe/.agents/plan.md.
- No wildcard CORS/browser security bypass, no direct backend-service requests, no port/Gateway-prefix changes.
- No Django/database/migration/dependency/lockfile/CI changes. Gateway writes are limited to reverting this agent's interrupted CORS changes.
- No real credentials or live login calls. Preserve existing/concurrent user changes and commits.

## Acceptance criteria
- Browser requests use its frontend origin, e.g. http://localhost:5173/auth/login/; Vite forwards to Gateway :8000/auth/login/.
- Tests verify proxy path/method/body/Bearer forwarding and that frontend routes remain SPA routes.
- Axios base URL is `/` unless explicitly overridden. Local .env uses `/`.
- Lint, full frontend tests, TypeScript/build and Gateway discovery regression tests pass.
- No live Gateway restart; source remains at its prior non-CORS behavior after selective rollback.

## Assumptions and risks
- Vite proxy fixes local development. Production must proxy API prefixes on the same origin or configure server CORS for an explicit cross-origin API URL.
- Gateway/Consul/upstream availability still determines actual login success.
- Vite must restart to load config/environment changes. Do not stop a user-owned frontend process without identifying it; report restart if necessary.
- No connected browser was available previously; automated local HTTP integration can verify proxying but not real-account login.
- The repository may have committed changes during interruption; never use git reset/revert to undo unrelated work.
