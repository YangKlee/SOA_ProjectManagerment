# Plan: Fix topic display-name enrichment

Status: Complete after initial and expanded user approvals `ok`.

1. Confirm plan for academic-to-auth name lookup config, regression tests/docs and verified restarts.
2. After approval, inspect runtime topic-owned Topics references without printing personal data; call academic read-only POST /api/v1/topic-display-names/ and auth read-only POST /internal/v1/user-display-names/ with existing authorized JWT/internal credentials held in memory. Compare healthy discovered auth address and localhost reachability using bounded timeouts; report statuses, timing and name-present booleans only.
3. If localhost names succeed while discovered auth address fails, change only ignored academic-service .env AUTH_NAMES_DISCOVERY_ENABLED=false and AUTH_NAMES_BASE_URL=http://127.0.0.1:8001. Snapshot only these nonsecret original entries in memory for rollback; verify unrelated dotenv values unchanged. Preserve auth/identity-management/JWT/internal credentials and all Consul/Gateway code/config defaults.
4. Add academic config/client regression tests for explicit local auth names endpoint, service-local dotenv and process-env precedence, correct internal credential forwarding and safe fallback. Add/update topic names response regression coverage as required, retaining major/advisor field contracts and nulls for missing names. No source policy or public API changes planned.
5. Update academic/topic service READMEs and root troubleshooting for independent identity-management versus display-name clients and Windows local endpoints. Document nested timeouts and genuine null cases accurately.
6. Run each affected service venv python -B manage.py check and python -B manage.py test; mock dependencies and use disposable DB fixtures only.
7. Restart only verified academic runserver listener/tree on 8002 with its original executable/bind/cwd, hidden. If needed restart verified topic on 8004 to clear display-name circuit; do not restart auth or unrelated processes. If process identity cannot be safely verified, report manual restart requirement.
8. Verify runtime read-only academic batch and topic list return real names for existing named references; absent references remain null. No create/update/delete requests. Ensure wrong/missing credentials still rejected through tests, .env ignored, no unrelated file changes; record findings/results/limitations.

## Expected files
.agents/task.md, .agents/plan.md; ignored services/academic-services/.env (two AUTH_NAMES keys); academic config/display-client tests; topic display-name tests if needed; services/academic-services/README.md, services/topic-service/README.md and root README.md. No frontend, auth source/env, database, lockfiles or infrastructure.

## Rollback
Restore original academic AUTH_NAMES entries and restart same verified academic instance; restart same topic instance only to clear circuit as needed. Revert only task tests/docs; preserve previous topic loopback validation fix and all user changes. Missing data is reported, never repaired silently.

## Approval boundary
Root AGENTS.md requires explicit confirmation before configuration/source/docs edits, external service calls and restarts. Only .agents/task.md and .agents/plan.md are written before approval. The new academic config/restart scope was not included in the previous approved topic-only change.

## Approval update: extra auth restart
Initial user `ok` approved diagnostic probes and academic/topic name-lookup work. Probes confirmed Windows discovery failure AND local auth 403 with matching configured credentials. The original plan excluded auth restart, so its authorization is now explicitly requested. No source/env changes have been made for this task before resolving this expanded scope.

Revised ordered steps after additional approval:
1. Read effective auth configuration in an isolated process without outputting secrets; identify the active 8001 listener ancestry and verify exact service executable/bind.
2. Restart only that auth runserver tree, hidden, with original executable, cwd and 0.0.0.0:8001. No auth source/env/key changes. Check empty read-only internal lookup with correct credential returns 200 and wrong/missing credential returns 403.
3. Once localhost auth works, set only academic .env AUTH_NAMES_DISCOVERY_ENABLED=false and AUTH_NAMES_BASE_URL=http://127.0.0.1:8001, preserving all other fields. Perform original academic/topic tests, docs and verified restart steps.
4. Run auth Django check/tests as appropriate alongside academic/topic suites; use existing disposable fixtures. Confirm runtime existing topic returns real major/advisor names. No writes to production data.

Rollback addition: auth config is unchanged; restart does not require credential/schema rollback. If auth fails to start, restore original command with same current .env and report startup error safely. Do not terminate unrelated or duplicate idle processes; choose the listener's verified ancestor tree. The existing academic two-key rollback remains applicable after that edit.

AGENTS.md requires explicit confirmation of materially changed scope. Request is for one additional service restart, not permission to alter auth settings/data or bypass service credentials.

## Completed implementation and verification
- Both original display-name plan and extra auth restart explicitly approved by user `ok`. No auth source/environment/key or database changes were made.
- Verified two auth trees were simultaneously bound to port 8001: listener metadata showed the new process, but an established raw TCP connection identified the old process still serving stale credentials. Stopped only verified old serving auth trees and retained fresh auth. Correct internal credential now returns 200; wrong/missing credentials return 403.
- Changed only academic ignored .env AUTH_NAMES_DISCOVERY_ENABLED=false and AUTH_NAMES_BASE_URL=http://127.0.0.1:8001; boolean comparison verified unrelated settings unchanged. Both entries were originally absent; rollback removes these two entries. JWT/internal credentials and AUTH_IDENTITY_* unchanged.
- Academic also had two verified serving trees on 8002. Listener plus established-connection PIDs identified both; restarted them as one instance with original venv/cwd/0.0.0.0:8002, hidden, using -B. Restarted verified topic loopback 8004 to reset display circuit. No unrelated processes stopped.
- Added 3 academic settings tests, 2 academic name-client tests and 2 topic enrichment/recovery tests. Updated root/academic/topic READMEs.
- Auth: manage.py check passed; 31 tests passed. Academic: check passed; 142 tests passed. Topic: check passed; 45 tests passed. Total 218 tests; disposable fixtures/mocked dependencies. Existing short signing-key warnings and mocked dependency warnings are not test failures; keys were not rotated.
- Runtime: all three health endpoints 200; academic batch 200 in 0.049s with both real names present. Two topic list calls returned 200 in 0.080s/0.075s with the existing topic's major_name and avisor_name present and matching academic. Auth internal names 200; missing/wrong internal credentials 403. No personal names/tokens/keys printed.
- Topic-owned references inspected through Topic ORM only; other owners' names queried through published read-only HTTP batch contracts. No production data writes, topic creation, migrations or schema changes.
- git diff --check passed; academic .env remains ignored. Frontend, gateway and registry configuration unchanged. Genuine missing identities/empty names and future dependency outages retain documented nullable behavior; nested timeout tuning was not changed.

- Final duplicate-instance check also found an old topic tree still accepting port 8004 alongside the fresh instance. Verified both service ancestries, stopped only old serving tree, retained fresh root 16028, and repeated authenticated GET: 200, existing topic count 1, both major/advisor names present. One fresh instance per affected service remains.
