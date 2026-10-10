# Task: Restore topic major/advisor display names

Status: Complete after initial and expanded user approvals `ok`.

## Objective and read-only findings
Fix topic responses returning major_name:null and avisor_name:null for existing named academic references. Topic obtains both names through academic's read-only batch endpoint; academic obtains lecturer user names through auth's service-authenticated internal batch endpoint. Academic still has AUTH_NAMES_DISCOVERY_ENABLED=true, while auth advertises host.docker.internal. Earlier runtime evidence established this hostname was unreachable from local Windows Django callers. Topic's academic client is already explicitly loopback following the previous approved fix. JWT keys and INTERNAL_SERVICE_TOKEN match in local config (boolean-only verification).

Both outer topic-to-academic and inner academic-to-auth timeouts currently default to 2 seconds. If inner discovery/auth lookup stalls, the outer call can time out first and discard both name maps, even when the major exists. This explains a possible path to both null values; current runtime batch responses and referenced row existence still need verification after approval.

## Scope
- After approval, diagnose with bounded read-only batch calls: topic-owned references, academic batch response and auth internal names, comparing discovered versus local auth endpoint. Do not print tokens, personal names or secret values; output statuses and availability booleans.
- If confirmed Windows discovery reachability failure, change only academic local .env AUTH_NAMES_DISCOVERY_ENABLED=false and AUTH_NAMES_BASE_URL=http://127.0.0.1:8001. Preserve identity-management client settings, JWT/internal keys, topic's academic config and registry/Gateway defaults.
- Restart only verified academic runserver instance on 8002 with original bind/executable/cwd. Restart verified topic instance on 8004 if necessary to clear its existing display-name circuit after recovery. Preserve original bind addresses; hidden windows.
- Add academic display-client/config regression tests and topic response/fallback tests where needed. Update affected READMEs/root troubleshooting. Keep current JSON avisor_name spelling and null behavior for genuinely missing references/names.
- Verify both services' Django checks/tests and runtime topic name enrichment on existing records without creating/updating any data.

## Constraints and acceptance criteria
No auth source/env changes, no frontend changes, no DB/schema/migrations, dependencies or infrastructure changes. No direct cross-service DB/ORM access: topic reads only Topics and relation IDs; academic/auth details obtained via their published REST lookup contracts. No real account/topic writes. Successful named references must return real major/advisor names; absent names remain null, not fabricated IDs. Authorization and bounded network behavior remain intact. Automated tests/checks pass.

## Assumptions and risks
Latest evidence indicates a second Docker-hostname/local-process mismatch, now academic-to-auth. Runtime confirmation is required before changing config. Brief academic/topic downtime for verified restarts. Some rows may genuinely lack corresponding identities or stored names; report those without modifying data. Equal outer/inner per-call budgets remain a deployment tuning consideration; do not hide outages by inventing names or bypassing security. Materially different code/API changes need a revised plan.

## Runtime findings after approval
- Topic-owned read-only sample contains one topic with major/advisor references. No data was printed or changed.
- Healthy discovered auth address is host.docker.internal:8001 and fails from Windows with URLError after about 2 seconds.
- Local auth internal name lookup returns 403 with current nonempty INTERNAL_SERVICE_TOKEN from auth, academic and topic local configs; the three configured values match. Even an empty read-only lookup is rejected before any data access. This is a second blocker beyond discovery; running auth credentials appear inconsistent with current file configuration.
- Academic batch completes after about 4 seconds with the major name present and advisor name null. Current topic GET also has major name present and advisor name null. The equal outer/inner timeouts explain why earlier results can lose both names.
- Auth listener on 8001 belongs to a verified local auth-service runserver tree. Existing scope explicitly excluded auth restarts; no service has been restarted and no environment/source file changed during this task yet.

## Proposed additional scope requiring approval
Permit restarting only the verified auth-service listener/process tree on 8001 with the current auth venv, original 0.0.0.0:8001 bind and service cwd, hidden, to reload current credentials. Do not change any JWT key, INTERNAL_SERVICE_TOKEN, auth source, auth .env or account data. Then verify local internal lookup accepts current credential and rejects wrong/missing credentials. If it succeeds, perform the already proposed academic AUTH_NAMES loopback config, academic restart, optional topic circuit reset, tests/docs and runtime verification. If restart does not reconcile credentials, stop dependent changes and report further evidence rather than bypassing auth.

## Outcome
Existing topic verified twice with both real major/advisor names populated after correcting local names transport and removing stale duplicate serving instances. All three Django checks and 218 tests passed. No database/user/topic data changed. See plan.md for runtime evidence, approved restart scope and rollback details.
