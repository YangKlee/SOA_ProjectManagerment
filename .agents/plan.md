# Plan: Topic response names through academic-service

Status: Completed after user approval (`ok`). Steps 1-7 are complete.

## Ordered steps
1. Add an explicit display-name-only DTO and read-only batch endpoint in auth-service. Use constant-time service-token comparison, deny when unconfigured, and constrain request size/ID count. Preserve public auth contracts.
2. Add an academic batch name-resolution endpoint protected by existing JWT authentication, accessible to authenticated readers even though POST carries a read-only batch. Query only academic-owned Majors and Lecturers. Resolve lecturer identity names through the new auth contract using the dedicated service credential, Consul discovery, bounded 2-second per-call timeout and safe failure handling. No cross-service ORM.
3. Extend topic's HTTP client to fetch names from academic in batches of <=100 IDs with per-request deduplication and one discovery resolution per enrichment operation. Reuse the existing timeout, circuit/failure conventions and redirect protections. Keep write validation separate from optional name resolution.
4. Replace response fields with nullable major_name and avisor_name. Supply enriched DTO data outside the serializer; keep network access outside serialization and outside write transactions. Apply to list/detail and successful write responses. Return null for missing/unavailable names, without replacing IDs in storage or request DTOs.
5. Add automated tests in all three services for exact response fields, batch deduplication, correct full-name composition, nullable advisor, missing references/names, authentication/role behavior, internal-token security, discovery/timeout/malformed payloads and fallback after successful writes. Use mocked network and disposable databases only.
6. Update root/service READMEs, .env.example files and task/plan status. Describe breaking response changes, exact spelling, internal contract, environment credential setup, lookup limits, timeout/call counts, and fallback semantics.
7. Run each affected service's installed Python environment: python manage.py check and python manage.py test. Review scoped git diff --check and ensure no database, migration, dependency, gateway or unrelated files changed. Existing CI already covers all three services; change CI only if verification commands change.

## Expected files
- topic-service/topic_manager/{serializers,views,clients,tests}.py; dedicated enrichment module if useful; topic-service README and .env.example.
- academic-services/config/{urls,settings}.py; new display-name DTO/view/client/test module(s) within LectureManager or a local lookup package; academic README and .env.example.
- auth-service/config/{urls,settings}.py; authentication display-name DTO/view/permission/test additions or dedicated local module(s); auth README and .env.example.
- Root README.md, .agents/task.md and .agents/plan.md.
No schema, model mapping, migration, dependency or infrastructure changes are planned.

## Verification and rollback
Check/test all three affected services, mocked contract/security/failure tests, DTO field assertions and batched lookup counts; preserve existing CRUD regression coverage. No live service calls or real database writes. Revert only this task's reviewed file-specific changes to restore ID responses and remove the new optional contracts/settings; preserve prior CRUD implementation and unrelated work. There is no data/schema rollback.

---

# Current plan: Admin login diagnosis and minimal fix
Status: Awaiting explicit approval. Earlier topic-name plan remains pending.

1. Obtain the failing admin UserId/email and confirm whether the running auth-service uses this checkout and database (no password requested).
2. Inspect only the relevant auth-owned record in read-only mode; report presence, role and password format without disclosing credentials. Inspect startup/database selection as needed without reading or printing secrets or calling external services.
3. Reproduce any identified code defect with mocked Users data and add a focused regression test. Apply a minimal fix only if it preserves the existing plaintext login contract. If diagnosis requires creating/resetting an account, supporting password hashes, or changing database configuration, update task/plan and obtain explicit approval for that concrete scope first.
4. For a code fix, run venv/Scripts/python.exe manage.py check and manage.py test in services/auth-service; check the scoped diff. Update documentation only if behavior changes and has been approved.
5. Record findings and remaining limitations. Do not modify the shared database during tests.

## Expected files
.agents/task.md and .agents/plan.md. Conditionally services/auth-service/authentication/views.py and authentication/tests.py for a confirmed compatible login defect. No other files are authorized by this plan.

## Verification and rollback
Use isolated mocked account fixtures for role 1 success, invalid credentials, token role, refresh/profile and existing login regressions. Revert only changes from this task; preserve existing work. No database rollback is needed because this plan authorizes no database writes.

## Verification results
- topic-service: manage.py check passed; full manage.py test passed (37 tests).
- academic-services: manage.py check passed; full manage.py test passed (116 tests).
- auth-service: manage.py check passed; full manage.py test passed (23 tests).
- All HTTP tests mock transports; topic persistence regression tests use disposable SQLite. No live external service calls or real database writes were required.
- Scoped diff/whitespace checks passed. Existing CI already covers these commands; no CI/dependency/schema/gateway updates needed.
- Added per-cache lookup quotas and bounded JSON parsers within the approved contract/resource-limit scope.
- Runtime setup still requires a matching service token in auth/academic environments; live integration remains unverified.
