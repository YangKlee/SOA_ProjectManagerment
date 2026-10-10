# Task: QNU login UI and page branding

Status: Completed after user approval (`ok`).

## Objective
Match the supplied QNU login reference using public/img/banner_QNU.jpg and public/img/logo.png; use the QNU logo for the browser page icon and dashboard menu branding.

## Scope
- Desktop login: large campus banner at left (approximately two thirds), light gray panel at right, centered university logo/name, white login card, red heading, navy submit button and footer.
- Responsive tablet/mobile layout, accessible labels, validation, loading/error states and existing password visibility control.
- Browser favicon and dashboard sidebar university logo; review dashboard-menu.ts and centralize shared branding there if appropriate, preserving role menus and routes.
- Automated UI/regression tests and frontend README notes.

## Constraints
- Before confirmation, write only .agents/task.md and .agents/plan.md.
- Preserve existing login API, credentials DTO, sessions, role guards, routes and unrelated working-tree changes.
- No backend, database, dependencies, lockfiles, migrations or infrastructure changes. index.html favicon metadata is explicitly in scope.
- Use existing supplied image assets without modifying them or fetching external assets.

## Acceptance criteria
- Login visually follows supplied reference at desktop and remains usable on small screens without horizontal overflow.
- Both supplied assets are correctly referenced; favicon and sidebar branding use logo.png.
- Validation, password toggle, duplicate-submit protection, server errors, login redirects and authorization regressions remain covered by tests.
- Frontend tests, lint and build pass; visual review at desktop and mobile where tooling permits.

## Assumptions and risks
- Page icon means browser favicon; dashboard-menu.ts reference means shared dashboard/menu branding, not replacement of every functional menu icon with the university logo.
- No Google login or password-reset integration is currently present. Show the reference's secondary controls disabled with a clear unavailable explanation; implementing these flows requires a separate plan.
- Reference shows validation after interaction; initial form must not show required errors before submission.
- Existing working tree contains ongoing dashboard/academic work; preserve all unrelated edits.
- Banner cropping and panel proportions must adapt to viewport sizes. Footer must not credit an unrelated vendor from the sample.

## Completion and verification
- Updated QNU login banner, university header, white card, navy submit, red heading and responsive styles. Existing authentication behavior and accessible validation remain intact.
- Added logo favicon and replaced dashboard sidebar text branding with logo.png, shared via QNU_BRANDING in dashboard-menu.ts.
- Google login and password reset are disabled with visible explanation; no API or architecture changes.
- Added branding and secondary-action tests; existing role menu, authorization, redirect and authentication regressions pass.
- Focused suite: 82 tests passed. Full suite: 179 tests passed across 10 files. npm run lint and npm run build passed.
- Build favicon metadata and copied image bytes verified; scoped git diff --check passed (line-ending warnings only).
- Browser visual verification unavailable: in-app browser was unavailable and connected browser inventory was empty. Desktop/mobile styling has not been screenshot-verified.
- Updated frontend README only; existing unrelated changes were preserved. No Django checks apply to this frontend-only change.
