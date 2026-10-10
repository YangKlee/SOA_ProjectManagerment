# Plan: Restore local topic display-name enrichment

Status: Awaiting explicit user approval.

## Ordered steps
1. After approval, recheck the topic-service .env setting and listener/process identity on port 8004; preserve all unrelated work.
2. Change only ACADEMIC_DISCOVERY_ENABLED to false in services/topic-service/.env. Keep ACADEMIC_BASE_URL=http://127.0.0.1:8002 and all secrets/other settings unchanged.
3. Restart only the verified topic-service development process using its existing Python environment and startup address/port. Recheck ownership before stopping processes; launch hidden if using Start-Process.
4. Verify effective settings, topic/academic health and actual read-only display-name resolution using existing published contracts without printing credentials or changing data. Use each service only for its own data boundaries; do not manufacture JWTs or bypass authorization.
5. Run relevant existing configuration tests and Django check in topic-service. Record results and any remaining unavailable live verification in task/plan; report exact resolution.

## Expected files
- fe/.agents/task.md and plan.md
- services/topic-service/.env (one local setting, untracked; never commit or display secrets)
- No source, database, infrastructure or dependency edits. Existing README already documents this exact local-development setting.

## Verification
- Configuration test config.test_academic_config and python manage.py check using existing service environment.
- Confirm academic health on loopback and restarted topic health on 8004.
- Confirm real names through authorized read-only lookup if an existing identity/session is available; do not mint live user JWTs. Otherwise verify the lookup transport and state the remaining authenticated UI check clearly.
- Preserve existing CRUD work and database. Do not create/edit/delete records for diagnosis.

## Rollback
Restore only the previous ACADEMIC_DISCOVERY_ENABLED=true value in the local topic .env and restart the same verified topic-service process. Other services/configuration and ongoing source changes stay untouched.
