# Plan: Gender/status dropdown controls

Status: Completed after user `ok` approval.

1. Update shared UserProfileFields to provide select options for user.gender (Nam1, Nu0) and user.status (Hoat dong1, Khoa0) using existing AcademicFormField.
2. Change field labels to plain gender/status labels and preserve required/nullable handling and existing numeric DTO conversion.
3. Add/update student/lecturer popup tests for labelled options, add/edit numeric1/0 payloads, zero-value prefill and null behavior. Update frontend README option documentation.
4. Run npm run lint, npm run test and npm run build; inspect diff and record results.

## Expected files
fe/src/features/academic/components/UserProfileFields.tsx, academic-config.ts, AcademicPages.test.tsx, fe/README.md, .agents/task.md and .agents/plan.md. AcademicFormField.tsx only if needed to display the existing labels cleanly. No backend, database, migrations, dependencies, environment or infrastructure changes.

## Rollback
Revert only this task's select/label/test/documentation edits; preserve previous user profile lifecycle, shared-token and connectivity work. No data rollback is needed.

## Approval boundary
Per repository AGENTS.md, only task/plan files are written before the user explicitly confirms this plan.

## Verification and delivery
Shared UserProfileFields now supplies gender/status options to AcademicFormField, displaying plain labels. Gender Nam1/Nu0 and status Hoat dong1/Khoa0 submit numeric values through existing DTO conversion. Empty/null and unexpected legacy values remain compatible; zero values prefill correctly. Both student/lecturer create and edit mappings are covered by regression tests. Frontend README updated.
Frontend lint passes, all153 tests across10 files pass, production build passes, and git whitespace check passes. No backend/API/schema/login-policy changes, real account operations or service restarts performed in this task. Previous unrelated work preserved.
