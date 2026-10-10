# Plan: Revise dashboard menus by role

Status: Completed after user approval (`ok`).

## Ordered steps
1. After approval, recheck current files and working tree to preserve concurrent work.
2. Replace DASHBOARD_MENU with the requested role 1/2/3 entries; support rendering role 3 without a group heading.
3. Separate the profile selection item from business menu order. Update header/welcome profile actions and derive quick access cards from the revised menu.
4. Update layout tests to verify the complete business menu for each role, removed entries, role 1 independent group expansion, role 3 selection, shortcuts, profile actions and mobile drawer interactions. Preserve login/role-guard/logout regressions.
5. Update frontend README with the exact menu structure and profile access behavior.
6. Run npm run lint, npm run test, npm run build and scoped git diff --check. Record results and implementation limitations in this plan.

## Expected files
- .agents/task.md, .agents/plan.md
- src/components/layout/dashboard-menu.ts
- src/components/layout/MainLayout.tsx
- src/components/layout/MainLayout.test.tsx
- README.md (dashboard section only)

## Verification
- Full menu content/role isolation checks, not just one example label.
- Role 1 group collapse preserves active selection and the other group.
- Role 3 standalone registration entry and shortcut open the correct placeholder.
- Profile controls open the explicit profile placeholder for all roles.
- Mobile drawer selection/dismissal, keyboard focus and logout remain verified.
- npm run lint; npm run test; npm run build; scoped diff review/check.
- No Django checks apply to this frontend-only task.

## Rollback
Undo only menu restructuring and related JSX/tests/README edits from this task, restoring the prior dashboard behavior. Preserve the existing dashboard implementation and unrelated frontend/backend/user changes. No database or infrastructure rollback is needed.

## Verification results
- Implemented exact role business menus and standalone student registration entry.
- Profile actions now use PROFILE_ITEM, independent of business menu order; quick access cards use current role menu items.
- Updated layout tests verify complete ordered menus, role isolation, shortcut destinations, profile actions for all roles, independent admin group collapse and mobile registration selection.
- Targeted layout/auth integration tests: 38 passed.
- Full frontend suite: 6 files, 78 tests passed.
- npm run lint: passed. npm run build (TypeScript and Vite): passed.
- Scoped git diff --check: passed with line-ending normalization warnings only.
- Frontend README updated. No backend/API/route/authentication/config/dependency changes in this task; unrelated edits preserved.
- Remaining limit: business pages are placeholders, not working CRUD/API integrations. No browser rendering verification performed in this task.
