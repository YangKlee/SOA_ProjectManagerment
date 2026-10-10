# Task: Proper frontend page routing

Status: Complete after user approval `ok`.

## Objective and evidence
Replace MainLayout's selected-menu local state with explicit React Router routes so each page has a stable URL, direct links/F5 preserve the current page, and browser history works. Existing App defines only /login, /admin, /lecture and /student; MainLayout currently swaps academic pages without changing location.

## Scope and route contract
- Preserve /login and role roots /admin, /lecture, /student as overview pages.
- Admin academic pages: /admin/departments, /admin/majors, /admin/students, /admin/lecturers.
- Profile routes: /admin/profile, /lecture/profile, /student/profile; retain current development placeholder content (no new profile API/UI implementation).
- Existing undeveloped menu entries get explicit placeholder routes: /admin/topics, /admin/registrations, /lecture/topics, /student/registrations. Do not claim these business features are implemented.
- Use nested role-protected layout routes and Outlet. Centralize route/menu metadata, use real links/NavLink, derive active item/title/breadcrumb from location, and extract overview/placeholder content from the layout shell.
- Keep session restoration guard before protected pages render. Preserve intended allowed deep links through login using validated internal route state; wrong role redirects to its own overview. Root / redirects according to session. Unknown paths show an explicit404 page with appropriate navigation.
- Preserve mobile drawer closing, focus trap/return, account panel, quick links, existing academic popup behavior and request cancellation on page navigation.
- Update route/layout/auth integration tests, frontend README/root frontend guidance and frontend deep-link proxy tests as needed. Document production SPA fallback requirement without changing server/infrastructure config.

## Constraints
Frontend only. No dependencies, lockfiles, backend/API routes, credentials, environment settings, database, service restarts or infrastructure changes. Keep existing role roots (including /lecture) compatible. Never accept external/arbitrary return URLs or expose admin pages to other roles. Keep all earlier user work.

## Acceptance criteria
Each implemented academic page has a working URL and navigation link. Direct navigation/session restoration renders the correct page; F5 retains pathname and session. Back/Forward updates page, active menu and breadcrumb. Login returns to a known authorized requested page; no external/open redirect. Wrong-role/unauthenticated access remains guarded. Unknown routes visibly404. Known undeveloped pages remain clearly labelled placeholders. Existing mobile/keyboard and academic CRUD tests pass. Frontend lint/full tests/build pass; no real account CRUD required.

## Assumptions and risks
/admin/departments is chosen to match the existing DepartmentPage and API terminology; menu label remains Quan ly khoa. Route changes can affect sidebar semantics and focus handling, so tests must cover anchor links and drawer controls. Production hosting needs history fallback to index.html for frontend URLs; backend gateway prefixes must remain untouched. No hosting deployment is included.
