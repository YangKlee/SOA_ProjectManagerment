# Plan: Composite student/lecturer and identity management

Status: Awaiting explicit approval.

## Ordered implementation
1. Finish scoped read-only inspection of schema SQL/indexes, auth/academic security, DTO/test conventions and relevant downstream references. Verify enum/value assumptions; retain unmanaged table mappings and unchanged schema.
2. Define versioned contracts: internal auth identity CRUD/batch lookup with service token + role-1 caller validation; composite academic /api/v1/students/ and /api/v1/lecturers/ CRUD with nested safe user DTOs. Support string IDs in the new version while preserving old numeric student routes. Document request/response/error formats, password behavior, role restrictions, body/batch limits and operation failure states.
3. Implement auth-owned Users application operations/DTOs/views and safe integrity handling. Reuse its existing unmanaged model; adjust its mapping documentation only where needed. Assign student/lecturer roles server-side; protect immutable IDs, unrelated users/admins, secrets and audit/business references.
4. Implement academic identity REST client using Consul and environment-supplied service credentials, finite timeouts, redirect/response bounds, rate expectations, correlation IDs and bounded circuit behavior; never retry writes automatically.
5. Implement composite workflows in StudentManager/LectureManager: validate academic inputs first, perform owned-table writes and authenticated identity REST calls in an explicit order, compensate confirmed failures where safe and return conflict/unavailable/incomplete states on uncertain outcomes. Never hold a SQLite write transaction across REST. Keep legacy endpoints compatible.
6. Add explicit Gateway denies for auth internal management paths, without changing public login/refresh/me or service prefixes. Update Gateway unit and real-Nginx integration tests.
7. Extend frontend academic API types and student/lecturer pages/popups with safe identity fields, create password/edit optional password, response-only timestamps if shown, backend field errors, code/name Search and complete-delete handling. Preserve F5 session restoration and existing department/major behavior.
8. Add automated backend contract/service/client tests, isolated SQLite integrity/compensation tests and frontend CRUD/popup tests. Update existing role, auth and legacy-contract regression assertions.
9. Update root, auth, academic, Gateway and frontend READMEs plus affected .env.example settings. Update CI only if new test commands/dependencies are actually required; no package installation/schema change planned.
10. Run focused tests, relevant Django checks/full tests, Gateway unit/integration tests and frontend lint/full tests/build. Review diff/status and record any remaining operational configuration or recovery limitations.

## Expected files
- services/auth-service/authentication/: model mapping comment, new identity-management service/DTO/view/tests; config/urls.py and config/settings.py as required.
- services/academic-services/StudentManager/: serializers/services/views/urls/tests; models.py only if schema-consistent academic mapping correction is necessary.
- services/academic-services/LectureManager/: serializers/services/views/urls/tests; model remains academic-only.
- Shared academic client/workflow modules and tests under academic-service; config/settings.py and .env.example.
- auth-service .env.example and auth/academic READMEs.
- api-gateway/discovery.py and nginx.conf if bootstrap denies are needed; Gateway tests and README. Existing IPv4 discovery fix is retained.
- fe/src/features/academic/: typed DTOs/API, StudentPage, LecturerPage, field controls/config/styles and relevant tests.
- README.md, fe/README.md, .agents/task.md, .agents/plan.md; CI only if affected checks need changes.
- No database files, migrations, dependency locks or real environment secret files.

## Verification
- Auth/academic unit and API tests for successful lifecycle, validation failures, duplicate IDs/email/phone, wrong roles, service-token rejection, password omission and safe profile outputs.
- Owned-table mappings and NO ACTION constraints verified using isolated temporary databases; no service test may mutate the project database or query another service's tables from its application layer.
- Mock REST tests for discovery failure, timeouts, redirects, malformed responses, circuit state, create/update/delete failure ordering and compensation/uncertain outcomes. No request replay after a non-idempotent timeout.
- Gateway unit and isolated Nginx integration tests confirm internal management paths are blocked and public auth/academic routing still works with IPv4 settings.
- Frontend tests cover user fields in add/edit popups, optional edit password, safe prefill, code/name search, complete deletion, 409/503/incomplete errors and legacy department/major/F5 behavior.
- Run python manage.py check and python manage.py test in auth-service and academic-service with existing environments; inspect CI and run affected downstream tests if contracts require it.
- Run Gateway tests/Compose validation/build/isolated integration; frontend npm run lint/test/build.
- Review git diff --check/status; document any new environment values without exposing or modifying secrets. No live destructive CRUD tests.

## Rollback
Revert only this task's auth/academic/Gateway/frontend/documentation changes; retain previous academic UI, F5 session and IPv4 fixes. No schema rollback is required. Local service operations stay in isolated tests. If production schema changes or durable workflow storage become necessary, stop and submit an updated plan with backup/compatibility/locking/rollback details before proceeding.

## Approval boundary
Only task/plan files are written until approval. This plan explicitly includes auth-service/internal REST and frontend changes in addition to the two requested academic apps; it does not authorize direct Users access from academic-service, cascade deletion of linked business/audit data, or real user-data writes.
