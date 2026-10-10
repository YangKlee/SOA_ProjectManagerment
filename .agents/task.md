# Task: Return academic names in topic read responses

Status: Completed after explicit user approval (`ok`). Previous CRUD implementation is preserved.

## Objective and scope
Replace `major_id` with `major_name` and `advisor_id` with `avisor_name` (exact user-requested spelling) in TopicResponseDTO. Resolve names through academic-service HTTP contracts. Apply this response consistently to list/detail and CRUD write responses on existing and v1 topic routes. Write DTOs and database references remain IDs.

## Inspection evidence
- Academic MajorResponseDTO already contains `major_id` and nullable `name`.
- Academic LecturerResponseDTO contains only `lecturer_id` and `department_id`; Lecturers has no name column.
- FirstName/LastName belong to auth-service's Users table. No published arbitrary-user lookup currently exists.
- Consequently academic-service must obtain lecturer display names from auth-service through an authenticated contract; it cannot query Users directly. Topic-service will call only academic-service for names.

## Proposed contracts
- Add authenticated read-only batch lookup `POST /api/v1/topic-display-names/` in academic-service with `major_ids` and `advisor_ids` (maximum 100 unique IDs per array). Return ID-to-name maps; missing records/names map to null.
- Add service-authenticated read-only `POST /internal/v1/user-display-names/` in auth-service with up to 100 user IDs. Return only user IDs and display names composed from LastName then FirstName; never password, email, phone or other private fields.
- Authenticate the internal lookup with a dedicated environment-supplied service token; no configured token means deny all requests. Ordinary end-user JWTs alone cannot access it.
- Names are nullable. If optional name resolution is unavailable, preserve the main topic response with null names, log safe dependency diagnostics, and do not retry a completed write. Keep existing write-reference validation mandatory.

## Constraints
Only task/plan files may change before approval. Preserve ports, gateway prefixes, existing auth login/refresh/me contracts, existing JWT permissions and Topics ownership exception from the previous task. No schema/data changes, migrations, dependencies, containers, frontend changes or live external service calls. No cross-service ORM/table access. Never commit service credentials.

## Acceptance criteria
- Topic JSON includes major_name and avisor_name and omits major_id/advisor_id; request DTO still accepts IDs.
- Correct names returned for list/detail and write responses; absent advisor gives null, missing names and dependency outage have documented null fallback.
- Names are resolved in bounded batches with per-request deduplication, never one HTTP request per topic.
- Academic reads only its Majors/Lecturers; auth reads only Users; topic reads only Topics.
- New internal endpoint rejects missing/invalid credentials and ordinary JWT-only callers; output exposes display names only.
- HTTP calls use Consul discovery when enabled, explicit development URLs otherwise, bounded timeouts/body sizes, no redirects or blind retries, and safe errors.
- Add/update automated success, DTO, authorization, missing-name and dependency-failure tests; run check/test for all three affected services and diff checks.
- Update root and affected service READMEs and environment examples.

## Assumptions and risks
This is a user-requested breaking response change on both existing topic API variants. avisor_name intentionally follows the user's spelling. Names belong to current identity records, not historical snapshots. Auth dependency and service-token configuration expand scope beyond topic-service because academic currently has no lecturer names. Null fallback keeps reads and committed writes available during display-only enrichment failures. No name cache persists between requests; batch IDs are limited to 100 per call and deduplicated within each response. Network call counts scale by batches, which must be documented. Existing unrelated work must be preserved.

---

# Current task: Diagnose and fix admin (role 1) login
Status: Awaiting explicit approval; earlier topic display-name scope remains pending and is not part of this task.

## Objective and scope
Resolve the reported POST /login/ 401 for an admin account in auth-service. First establish which account and database the running service uses, then apply only an evidence-supported fix.

## Read-only findings
- Login looks up Users by email then UserId and compares plaintext passwords exactly. It contains no role-based login rejection.
- The configured repository database is database/DB_ProjectManagerment.db. A mode=ro inspection found 330 Users, all role 3; no role 1 account exists in this file.
- Existing mocked login tests already use role 1. Password hashes are intentionally unsupported by the documented current policy.

## Constraints
Preserve public routes, ports, JWT claims, password policy and service boundaries. Do not expose passwords or tokens. Preserve existing uncommitted work and the earlier pending task. No schema/model/migration/dependency/infrastructure changes. No production/shared database writes in the initial investigation.

## Acceptance criteria
Identify the account and active database causing the failure; reproduce with an isolated fixture where possible. Any code fix must include regression tests and pass auth-service manage.py check and manage.py test. If the account is absent or credentials differ, report that evidence and propose account provisioning/reset separately before making data changes.

## Assumptions and risks
The running server may use a different checkout/database, or the admin may not have been provisioned. Identifier and active database confirmation are needed; never request a password in chat. A role bypass cannot repair missing credentials. Do not claim the reported account is fixed until verified.

## Delivery and verification
- Topic response fields are major_name and avisor_name; request DTO and database IDs remain unchanged. All list/detail and successful write responses use the same enrichment.
- Added academic read-only batch name endpoint and auth service-token-only display-name endpoint. No cross-service table/model access.
- Added 64 KiB JSON body limits, 100-entry batch limits, process-cache throttles (120/min), bounded discovery/HTTP, redirect protection and separate display lookup circuits with null fallback.
- Added/updated endpoint, permission, DTO, batch/deduplication, missing-name, timeout, malformed-response, circuit, safe-error and committed-write fallback tests.
- Checks pass for all three services. Full test results: topic-service 37, academic-services 116, auth-service 23; all 176 tests passed.
- Scoped git diff --check and whitespace checks of new Python files passed. No database, model mapping, migrations, dependencies, gateway or CI changes in this task. Existing auth tests regenerated tracked bytecode; that artifact was restored to its original version.
- Existing frontend work was preserved. No real service credentials were created or modified, and no live external calls were made. For runtime lecturer names set matching DISPLAY_NAMES_SERVICE_TOKEN in auth and academic; missing credentials produce null advisor names.
- Live gateway/Consul/academic/auth integration was not exercised. Per-call timeouts and per-process circuits/quotas are not distributed total-deadline controls.
