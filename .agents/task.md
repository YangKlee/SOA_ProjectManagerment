# Task: User profile gender/status selects

Status: Completed after user `ok` approval.

## Objective
Use select controls in student/lecturer add/edit popups: gender Nam=1, Nu=0; status Hoat dong=1, Khoa=0, as specified by the user.

## Scope
Update shared frontend UserProfileFields so both pages use the same labelled selects. Preserve numeric/null JSON DTO behavior and safe edit prefill. Update frontend regression tests and frontend README field description. No backend authorization/login-policy or database changes.

## Constraints
Preserve all existing work, INTERNAL_SERVICE_TOKEN, APIs and popup behavior. Keep existing nullable contract: retain an empty option, and display legacy unexpected values without silently replacing them. A selected label must submit numeric1/0, never the label or string. Do not interpret status as a new login-lock enforcement policy; this task changes form controls only.

## Acceptance criteria
Both pages show gender/status as selects with the user-specified labels/mappings. Add/edit sends correct numeric values; existing values1/0 prefill correctly, including female/locked0. Clearing preserves null compatibility. Automated frontend tests for mappings/prefill pass, along with lint/test/build. No real account CRUD or service restarts required.

## Assumptions and risks
The user specifies UI options and their stored codes. Existing nullable/legacy records remain compatible through the current empty/unknown option handling. No enum/schema migration or reinterpretation of existing stored values is included.

## Verification and delivery
Shared UserProfileFields now supplies gender/status options to AcademicFormField, displaying plain labels. Gender Nam1/Nu0 and status Hoat dong1/Khoa0 submit numeric values through existing DTO conversion. Empty/null and unexpected legacy values remain compatible; zero values prefill correctly. Both student/lecturer create and edit mappings are covered by regression tests. Frontend README updated.
Frontend lint passes, all153 tests across10 files pass, production build passes, and git whitespace check passes. No backend/API/schema/login-policy changes, real account operations or service restarts performed in this task. Previous unrelated work preserved.
