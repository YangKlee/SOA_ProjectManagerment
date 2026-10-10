# Plan: Restore topic-to-academic validation in local development

Status: Awaiting explicit user approval of revised scope.

1. Confirm revised plan. Earlier UI approval did not authorize config changes, runtime probes or restarts. JWT file values now match; preserve them.
2. Use bounded read-only probes after approval: Consul healthy academic instances, sanitized discovered addresses, academic health and legacy detail DTOs through discovered address versus 127.0.0.1:8002. Keep tokens/keys in memory and output only status/class/booleans. Inspect topic listener/process identity and original startup command safely.
3. If evidence confirms Docker hostname unreachable from the Windows topic process and loopback academic valid, modify only ignored topic-service/.env ACADEMIC_DISCOVERY_ENABLED=false and ACADEMIC_BASE_URL=http://127.0.0.1:8002. Preserve original values in memory for rollback and verify every unrelated setting unchanged. No global Consul/Gateway changes.
4. Add topic config/client tests with dummy values for explicit static development config, environment precedence/service-local dotenv loading and reference validation success/errors. Keep discovery default enabled and mandatory JWT/reference checks. Update topic-service README and root README troubleshooting.
5. Run topic venv python -B manage.py check and python -B manage.py test using disposable test fixtures and mocked dependencies, no schema migrations or live DB writes.
6. Restart only the verified topic runserver tree on 8004, hidden, with its original executable/bind/directory. If identity/startup cannot be verified, report manual restart instead of stopping unrelated processes.
7. Verify health, read-only GET topics and academic reference DTO/validation calls with an in-memory short-lived test JWT issued using auth config. Do not log token or use real login credentials. Never POST a topic or modify accounts for verification.
8. Record results/limitations; review diff, ensure real .env ignored and all frontend changes preserved. If a different material cause is discovered, stop dependent edits and revise the plan for approval.

## Expected files
.agents/task.md, .agents/plan.md; ignored services/topic-service/.env (two academic client keys, conditional on diagnosis); topic-service config/client regression tests; services/topic-service/README.md; root README.md. No frontend, other service env, DB, package or infrastructure changes.

## Rollback
Restore only prior topic academic-client dotenv entries and restart the same verified topic instance; revert task-specific tests/docs only. Preserve user's JWT key correction and previous topic frontend work.

## Approval boundary
AGENTS.md Mandatory task workflow requires explicit confirmation before configuration/source/docs changes, calling external services or service restarts. Screenshot is diagnostic evidence, not explicit plan approval. Only the two permitted .agents files have been updated.
