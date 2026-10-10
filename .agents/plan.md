# Plan: URL-based frontend navigation

Status: Complete after user approval `ok`.

1. Inspect existing route guards, session/login navigation, dashboard layout/menu and tests; preserve role roots and session behavior.
2. Define central typed route metadata for overview, profile, four admin academic pages and existing placeholder menu entries; use consistent URLs listed in task.md.
3. Create nested role/layout routes with Outlet in App. Extract overview and placeholder content into pages; keep MainLayout as reusable shell. Add404 routing; retain root session redirect.
4. Replace state-driven sidebar/shortcut/account navigation with Link/NavLink. Derive active item/breadcrumb/title from URL, preserve mobile drawer focus/closing and keyboard support including anchors.
5. Preserve authorized requested deep links through login using safe internal route validation; keep role mismatch redirects and session restoration blocking stale navigation. Avoid open redirects.
6. Update/add router/layout/auth/academic integration tests for direct links, restored deep routes, allowed return destinations, unknown routes, Back/Forward, active menu/breadcrumb, mobile links and cancellation. Extend existing real Vite proxy deep-link tests if needed.
7. Update frontend README and relevant root frontend documentation with route table, placeholders, login return behavior and SPA history fallback. No hosting config changes.
8. Run npm run lint, npm run test and npm run build; review status/diff and record verification and remaining deployment limits.

## Expected files
fe/src/app/App.tsx, RoleHomePage.tsx (refactor/replace), new dashboard/placeholder/404 pages and route metadata; fe/src/components/layout/MainLayout.tsx, dashboard-menu.ts, dashboard.css only for link styling; fe/src/features/auth/AuthRoutes.tsx and login routing helpers as needed; related App/layout/auth/proxy tests; fe/README.md, README.md, .agents/task.md and .agents/plan.md. No backend, DB, packages, lockfiles, real .env or infrastructure.

## Verification and rollback
Use MemoryRouter/BrowserRouter integration tests and existing isolated Vite proxy tests; mock HTTP/session profile, never mutate real accounts. Validate navigation history and security cases, not only route metadata snapshots. Revert only this task's routing changes if needed, preserving previous CRUD/session/token/select work. Old role-root URLs remain valid throughout the change.

## Approval boundary
The task and plan were presented before implementation; user `ok` approved the scope. No further scope expansion was needed.

## Verification results
- npm run lint: passed (zero warnings).
- npm run test: 10 test files, 178 tests passed. Covers restored deep URLs, role guards, safe login return URLs/query/hash, all placeholders, 404, Back/Forward, request aborts and mobile navigation.
- npm run build: TypeScript and Vite production build passed.
- git diff --check: passed.
- Real Vite server proxy test serves nested frontend routes as SPA HTML and keeps Gateway API forwarding intact. No backend/API/config/database/dependency changes; Django checks are not applicable to this frontend-only task.
- Production hosting fallback and live backend/account behavior are not verified or changed; requirements documented in both READMEs.
