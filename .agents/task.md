# Task: Fix topic-service academic validation unavailable

Status: Complete after explicit user approval `ok`.

## Objective and evidence
Resolve screenshot response Academic validation is temporarily unavailable while creating a topic. The user's latest evidence supersedes the earlier JWT rejection. A fresh secret-safe local comparison now shows auth, academic and topic JWT_SIGNING_KEY values agree; do not overwrite these keys.

Topic client forwards the caller JWT to academic /api/majors/{id}/ and /api/lecturers/{id}/; route contracts match the current code. It returns this generic 503 for discovery/transport failures, academic 401/403/5xx and invalid DTOs, not only a stopped service. Current topic .env enables ACADEMIC_DISCOVERY_ENABLED=true and uses Consul localhost:8500; academic advertises host.docker.internal:8002. Windows academic listener is active on 0.0.0.0:8002. The registered Docker hostname is a suspected reachability mismatch, consistent with an earlier local identity-client issue, but current registry payload/runtime HTTP status have not been probed because approval is still pending.

## Proposed scope
After approval, first make bounded read-only runtime probes to distinguish discovery, address reachability, JWT rejection and DTO failures. If discovery returns an academic address unreachable from this Windows topic process while localhost academic succeeds, configure topic-service local .env ACADEMIC_DISCOVERY_ENABLED=false and ACADEMIC_BASE_URL=http://127.0.0.1:8002. This is explicit local-development config only; preserve Consul/Gateway registrations and code defaults. Preserve JWT_SIGNING_KEY, INTERNAL_SERVICE_TOKEN and all unrelated settings. Do not silently disable discovery in production code.

Restart only the verified local topic-service runserver on 8004 with its current executable, bind address and directory, hidden. Add automated configuration/client regression coverage and docs for this Windows development scenario. Verify topic checks/full tests and read-only runtime reference validation. No production topic/account writes.

## Constraints
No auth/academic/other service changes, no database/schema/migrations, dependency changes, frontend changes or infrastructure edits. No authentication bypass; public JWT and internal service credentials remain separate. No secret/JWT output or committed real .env. Preserve ongoing frontend work. If runtime evidence requires a materially different fix, update plan and obtain approval before it.

## Acceptance criteria
Identify actual upstream/discovery failure safely. Valid academic major/lecturer references can be checked from topic runtime using bounded REST requests, while nonexistent references remain 400 and invalid JWTs remain rejected. Existing tests/checks pass. No real topic writes needed to verify dependency validation; do not claim user's POST was retried or successful.

## Risks
Brief topic interruption during restart. Current .env and running process configuration can differ. Static loopback is appropriate only for services on this Windows host; container deployments must keep reachable discovery addresses. Optional display-name dependencies may fail independently of required validation. Topic creation may reveal another issue after validation recovers; handle it separately without bypassing ownership or constraints.
