# Plan: Configure Gateway CORS for frontend origins

Status: Awaiting explicit approval of revised Gateway plan. Earlier Vite-proxy proposal is superseded, not implemented.

## Ordered steps
1. After approval, verify official Nginx header/map/preflight semantics and inspect current Gateway runtime/readiness without exposing secrets.
2. Add strict CORS origin parsing and config rendering to discovery.py; read CORS_ALLOWED_ORIGINS once at startup and preserve it across generated config reloads.
3. Render exact-origin allowlist maps and CORS response headers with always semantics, Vary: Origin and bounded preflight cache. Handle preflight locally on existing API prefixes. Hide conflicting upstream CORS headers and retain proxy behavior.
4. Align checked-in bootstrap nginx.conf with local defaults; wire configurable origin allowlist in docker-compose.yml and .env.example. Preserve Gateway .env if present; update only an existing CORS override if necessary.
5. Extend Gateway unit tests for origin validation/empty list/config persistence and integration tests for allowed/denied preflight, actual errors, safe 503, Authorization/body forwarding and duplicate header prevention.
6. Update Gateway README, frontend README and root README CORS/run instructions. Preserve all unrelated changes.
7. Run Gateway unit tests, Compose validation and disposable image integration tests when Docker is available. Run frontend lint/tests/build. No Django checks because Django code is unchanged.
8. If Docker is available and Gateway can be deployed, rebuild/recreate only Gateway, verify nginx -t and live OPTIONS with allowed and disallowed origins. Do not submit real login credentials or recreate other services. Record any blocker.
9. Review scoped diff and update task/plan with evidence and limitations.

## Expected files
- fe/.agents/task.md, fe/.agents/plan.md.
- api-gateway/discovery.py, api-gateway/nginx.conf.
- api-gateway/docker-compose.yml, api-gateway/.env.example; only CORS override in api-gateway/.env if necessary.
- api-gateway/tests/test_discovery.py, api-gateway/tests/integration.py; additional focused CORS test file if useful.
- api-gateway/README.md, fe/README.md, root README.md (relevant sections).
- .github/workflows/python-tests.yml only if existing Gateway verification command needs adaptation; no unrelated CI changes.

## Verification
- Python standard-library Gateway unit tests, including existing discovery/resilience regressions.
- docker compose config --quiet; image build; isolated integration container with mock registry/backends; nginx -t.
- CORS checks for both localhost and loopback frontend origins, disallowed origins, missing Origin, auth/validation errors and unavailable upstreams; preserve routes/body/header forwarding.
- Frontend npm run lint, npm run test and npm run build with unchanged API URL.
- Live Gateway OPTIONS after Gateway-only recreation if possible. Browser QA only if connected; do not claim real-account login without testing.
- Scoped git diff --check; preserve database and concurrent edits.

## Rollback
- Revert only CORS changes, preserving existing discovery and unrelated edits.
- Restore only prior CORS environment setting if changed.
- Rebuild/recreate Gateway from previous config/image if a runtime rollback is required; no database cleanup or backend service changes.
