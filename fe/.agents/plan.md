# Plan: Switch to Vite development proxy

Status: Completed after user approval (`ok`). Proxy implemented and verified; CORS additions reverted. Running Gateway unchanged.

## Ordered steps
1. After approval, inspect current files and selectively remove only CORS additions introduced in the interrupted Gateway task; preserve pre-existing discovery and any concurrent changes.
2. Verify running Gateway image remains sha256:f4e70ed63d67ca3f447d35711d9d197a73a8a746d8d4bd8382ab2113acac16fc and restore soa-api-gateway:local to the non-CORS source. Docker cannot tag the old container image ID directly (image reference no longer present); rebuild restored source to restore the local image tag instead. No container restart/deletion.
3. Add typed Vite proxy configuration for `/auth`, `/academic`, `/registrations`, `/topics`, with configurable VITE_API_PROXY_TARGET defaulting to http://localhost:8000. Preserve paths/headers/body.
4. Wire proxy into Vite; change Axios default base URL to `/`. Update only API base URL in fe/.env and fe/.env.example; document optional proxy target.
5. Add automated local mock-Gateway/Vite integration tests proving forwarding and SPA-route isolation, plus client default/override regression tests.
6. Update frontend/root frontend documentation for proxy, restart requirements and production routing. No Gateway documentation changes were made before interruption, so preserve its existing content.
7. Run frontend lint/full tests/build and Gateway unit regression tests. Inspect scoped diff and record results; do not call real auth endpoints.

## Expected files
- fe/.agents/task.md and fe/.agents/plan.md.
- api-gateway/discovery.py, nginx.conf, docker-compose.yml, .env.example, tests/test_discovery.py, tests/integration.py: selectively revert this agent's CORS additions only.
- fe/vite.config.ts; proxy helper and tests in fe/src/config/ or fe/config/ as needed.
- fe/src/services/api-client.ts and relevant tests.
- fe/.env (API URL only), fe/.env.example.
- fe/README.md; root README.md frontend section only.
- Local image tag restoration only; no dependencies/lockfiles/CI/container changes.

## Verification
- Gateway Python unit tests after selective rollback.
- Proxy HTTP integration against ephemeral mock server, with no real credentials: path/method/body/Bearer preservation and frontend route isolation.
- Frontend npm run lint, npm run test, npm run build.
- Check existing .env value and proxy defaults without printing other environment values.
- git diff --check and scoped review. Report browser/live account verification limitations; Django checks do not apply.

## Rollback
- Revert only frontend proxy changes and restore prior frontend API URL if requested.
- Preserve prior login/role implementation and all unrelated edits/commits.
- Temporary verification servers close after tests. No broad git reset/clean, image removal or service recreation.

## Verification results
- Gateway CORS additions removed from generator/bootstrap/Compose/example environment/unit tests only. Integration test file was already back to its original non-CORS contents when this task resumed, so it was not changed.
- Original container image ID was not directly taggable in Docker's image store. Rebuilding restored source restored the local Gateway image; cached platform manifest matches the running container's original manifest. No container recreation/restart or image deletion.
- Gateway unit tests: 9 passed. Compose configuration validation passed.
- Frontend lint: passed. Full test suite: 5 files / 65 tests passed. Build including TypeScript: passed.
- Real Vite HTTP integration against an ephemeral mock Gateway: correct API target loaded from environment, preserved method/path/query/body/Bearer, preserved 401 status, and frontend SPA routes not forwarded. Temporary test servers closed automatically.
- Axios base URL tests cover absent/empty/whitespace/same-origin values and explicit absolute override.
- Local `.env`: VITE_API_BASE_URL=/, preserving other entries. Existing frontend server on localhost:5173 returns HTTP 200 for its client module with VITE_API_BASE_URL=/ loaded at runtime; no user-owned process stopped.
- Scoped diff review/check passed; no dependency/lockfile/CI/Django/database changes made. Pre-existing auth-service bytecode modification preserved.
- No real credentials or live login submitted; browser UI/real-account authentication unverified. Production requires same-origin API forwarding or separately configured server CORS.
