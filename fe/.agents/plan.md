# Plan: QNU login UI and page branding

Status: Completed after user approval (`ok`).

## Ordered steps
1. After approval, recheck current source and existing working-tree changes; inspect supplied asset dimensions and styling dependencies.
2. Replace login illustration with campus banner and implement university header/card/footer matching the supplied reference. Keep existing authentication behavior and accessible form states.
3. Style responsive layout and reference secondary controls, clearly disabled until corresponding services exist.
4. Add logo.png favicon in index.html. Use QNU logo for dashboard sidebar branding; define shared asset branding in dashboard-menu.ts if useful, preserving functional menu icons and role routes.
5. Add/update automated login and layout tests for branding, accessible form/validation and preserved authentication behavior; update frontend README with UI/secondary-control limitations.
6. Run focused tests, full npm run test, npm run lint, npm run build and scoped git diff --check. Review desktop/mobile rendering if available; record any verification limitation.
7. Record completion/results in these task files and report changed files and verification to user.

## Expected files
- .agents/task.md and .agents/plan.md
- src/features/auth/LoginPage.tsx and login.css
- index.html
- src/components/layout/dashboard-menu.ts, MainLayout.tsx, dashboard.css
- src/app/App.test.tsx and/or src/features/auth/LoginPage.test.tsx
- src/components/layout/MainLayout.test.tsx
- README.md (frontend UI notes only)
- public/img/banner_QNU.jpg and logo.png are inputs only; no asset writes planned.

## Verification
- Correct banner/logo references, favicon metadata and dashboard brand image.
- Accessible input labels, required errors after submit, password visibility, pending/error states and disabled secondary controls.
- Existing successful login, role/ownership guards, HTTP/network errors, cancellation and redirect tests.
- npm run test; npm run lint; npm run build; scoped diff check.
- Desktop/mobile visual review if available; no external services required.
- Django checks are not applicable: no backend changes in this frontend-only scope.

## Rollback
Revert only this task's source/style/metadata/test/documentation edits, preserving pre-existing edits in those files and all unrelated changes. No database, dependency or infrastructure rollback needed.

## Completion and verification
- Updated QNU login banner, university header, white card, navy submit, red heading and responsive styles. Existing authentication behavior and accessible validation remain intact.
- Added logo favicon and replaced dashboard sidebar text branding with logo.png, shared via QNU_BRANDING in dashboard-menu.ts.
- Google login and password reset are disabled with visible explanation; no API or architecture changes.
- Added branding and secondary-action tests; existing role menu, authorization, redirect and authentication regressions pass.
- Focused suite: 82 tests passed. Full suite: 179 tests passed across 10 files. npm run lint and npm run build passed.
- Build favicon metadata and copied image bytes verified; scoped git diff --check passed (line-ending warnings only).
- Browser visual verification unavailable: in-app browser was unavailable and connected browser inventory was empty. Desktop/mobile styling has not been screenshot-verified.
- Updated frontend README only; existing unrelated changes were preserved. No Django checks apply to this frontend-only change.
