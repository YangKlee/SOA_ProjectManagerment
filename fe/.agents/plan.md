# Plan: Login page and role routes

Status: Completed after explicit user approval (`ok`).

## Ordered steps
1. After approval, verify official React Router APIs and compatible version; install dependency and update npm lockfile.
2. Add auth DTO types and login API through `/auth/login/`; validate essential successful response fields and supported roles.
3. Add auth provider/hook with in-memory session and Axios token setter; implement login/logout without token persistence or refresh.
4. Implement Vietnamese login screen, accessible validation/errors, password visibility toggle, pending lock, and safe failure messages.
5. Add React Router, shared role mapping, protected routes, session-aware root/unknown redirects, and placeholder role home pages with logout. Use replace navigation after login.
6. Add/update tests for roles 1/2/3, exact payload, field validation, duplicate submission, 400/401, network/timeout, malformed/unsupported-role responses, guest/wrong-role redirects, authenticated login redirect, and logout. Keep existing Axios regression tests passing.
7. Document route graph, API usage, session behavior, and SPA deployment in frontend README; update only root README frontend section.
8. Run lint/tests/build, dev-server HTTP smoke checks, and browser review if available. Inspect scoped diff and record evidence/limitations.

## Expected files
- `fe/.agents/task.md`, `fe/.agents/plan.md`.
- `fe/package.json`, `fe/package-lock.json`: React Router dependency.
- `fe/src/app/App.tsx`, `fe/src/app/App.test.tsx`, role-home/routing components as needed.
- `fe/src/main.tsx` if needed for router/provider placement.
- `fe/src/features/auth/`: types, API, provider/hook, login screen, route guards, relevant tests.
- `fe/src/styles/global.css` and/or scoped login CSS.
- `fe/src/test/setup.ts` and existing Axios tests only if isolation/session integration requires it.
- `fe/README.md`; root `README.md` frontend section only.
- No backend/database/environment/workflow changes expected.

## Verification
- Focused auth/routing tests followed by full `npm run test`.
- `npm run lint` and `npm run build` (includes TypeScript).
- Mock HTTP requests; no real credentials or live auth calls in tests.
- Development server HTTP check including SPA fallback. Browser inspection if available; report limitation otherwise.
- Scoped `git diff --check` and review preserving existing user changes.
- No Django checks because no Django code changes. Existing CI commands remain valid; GitHub CI execution is not claimed locally.

## Rollback
- Revert only this task's changes, preserving the scaffold and existing user edits.
- Restore prior frontend package/lockfile entries if removing React Router.
- Remove only newly introduced auth/routing files and documentation sections from this task. No broad Git reset/clean.

## Verification results
- React Router 7.18.4 installed with matching npm lockfile. Installation audit: 0 vulnerabilities.
- Final `npm run lint`: passed.
- Final `npm run test`: passed, 3 files / 47 tests, including existing Axios regressions.
- `npm run build`: passed, including TypeScript. Initial type-check errors in test query options were corrected before the successful build.
- Vite starts on port 5173. HTTP GET of `/`, `/login`, `/admin`, `/lecture`, `/student` returns 200 with the React entry point (development SPA fallback).
- Browser discovery returned no connected browsers. Automated DOM tests cover login and role navigation; visual layout inspection remains unverified.
- No real credentials or live auth API calls used. Gateway/CORS/account integration remains unverified.
- Scoped `git diff --check`: passed. No backend/database/workflow edits made by this task. Other concurrent repository edits were preserved.
- Django commands not run because backend code was not changed by this task. GitHub CI has not been executed locally.
