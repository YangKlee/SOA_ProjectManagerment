# Task: Login page and role routes

## Objective
Create a Vietnamese login page with MSSV/UserID and password. Authenticate through the existing Axios client and route role 1 to `/admin`, role 2 to `/lecture`, role 3 to `/student`.

## Status
Completed after explicit user approval (`ok`). Login, in-memory session, role routes/guards, logout and mocked tests implemented. Lint, all 47 tests, TypeScript/build, and dev-server route HTTP checks passed. Live backend account integration and visual browser QA remain unverified; no browser is connected.

## Scope
- Add React Router, `/login`, and protected `/admin`, `/lecture`, `/student` routes.
- Build a responsive login form with required-field validation, show/hide password, loading state, duplicate-submit prevention, and safe errors.
- POST `/auth/login/` with `{ identifier, password }`, as confirmed in auth-service serializers/views/README. Trim identifier only; preserve password exactly.
- Read the confirmed response `{ access, refresh, token_type, user: { user_id, ..., role } }`; validate essential fields and supported role before creating a session.
- Store user and access token in memory; integrate the existing Axios token setter. Do not persist tokens or implement automatic refresh; ignore refresh token for now.
- Guests visiting protected routes go to login. Authenticated users visiting login or another role's route go to their own role home. Root/unknown routes follow the same session-aware default.
- Add minimal role landing pages and logout, without full dashboards or domain CRUD.
- Add mocked automated tests and update frontend README plus only the frontend section of the root README.

## Constraints
- Before approval, write only `fe/.agents/task.md` and `fe/.agents/plan.md`.
- Preserve existing user edits. No backend, database, migrations, ports, Gateway prefix, environment value, or workflow changes.
- Keep the requested route spelling `/lecture`.
- Backend determines role; do not add role selection or send client-chosen role in login payload.
- Frontend guards handle navigation; backend still enforces JWT and authorization.
- React Router installation and corresponding package.json/package-lock.json changes are included in scope.

## Acceptance criteria
- Accessible MSSV/UserID and password inputs; keyboard submission and loading feedback.
- Empty/whitespace-only identifier and empty password are rejected without requests. Password whitespace remains unchanged.
- Successful roles 1/2/3 navigate to their requested routes and set Axios Bearer token.
- Invalid credentials, validation errors, network/timeout, malformed response, and unsupported role fail safely without a session.
- Guest/wrong-role guards, authenticated login redirect, and logout work.
- Lint, all frontend tests, and TypeScript/build pass.

## Assumptions
- MSSV works when it is the account UserID; the backend has no separate MSSV lookup contract. No new lookup is invented.
- Session is in memory as established in the scaffold; reload requires login again.
- Gateway/CORS must be available for live login; mocked tests cannot prove live integration.
- Django checks do not apply because backend code is unchanged.

## Risks
- No browser was connected during the prior task; visual QA may remain unavailable.
- Production hosting needs SPA history fallback for frontend routes while preserving API forwarding.
- Preserve unrelated changes already present in root README/backend/root planning files.
