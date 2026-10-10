# Task: Restore topic advisor and major display names in local development

Status: Awaiting explicit user approval.

## Objective
Restore topic advisor/major display-name enrichment by correcting the local topic-to-academic connection, following the reported missing names after topic UI changes.

## Read-only findings
- TopicTable still renders avisor_name and major_name. No name columns were removed.
- The inspected topic retains major_id 1186 and advisor_id lecture in its owned Topics record.
- topic-service local .env enables ACADEMIC_DISCOVERY_ENABLED=true. Its configured ACADEMIC_BASE_URL=http://127.0.0.1:8002 is ignored in discovery mode.
- Consul resolves academic-service to http://host.docker.internal:8002; the health request from this Windows environment timed out.
- http://127.0.0.1:8002/health/ succeeds. Academic/auth local internal lookup credentials and JWT settings in their .env files are configured consistently (values not exposed).
- Optional enrichment catches dependency failures and returns null names, which the UI displays as an em dash.

## Scope
- Set only ACADEMIC_DISCOVERY_ENABLED=false in services/topic-service/.env, preserving existing local ACADEMIC_BASE_URL=http://127.0.0.1:8002 and all other settings/secrets.
- Restart only the verified local topic-service runserver on port 8004 so its process reloads .env.
- Verify effective local settings, academic reachability and read-only name enrichment; no real topic writes.
- Reuse documented Windows local-development configuration; no source, API, database or ownership changes.

## Constraints
- Before approval, write only current fe/.agents/task.md and plan.md.
- Never print credentials, signing keys, tokens or full environment files. Local .env remains untracked.
- Preserve Gateway/Consul registration, academic/auth service processes, ports and routes.
- Use static loopback only for this Windows local environment. Do not change discovery defaults in source or production configuration.

## Acceptance criteria
- Restarted topic process uses discovery=false and the existing loopback academic base URL.
- Name lookup reaches academic and returns real names for existing references where available; names remain nullable for genuinely absent identity data.
- Shared database and source remain untouched; existing topic CRUD changes preserved.

## Risks
- Restart briefly interrupts topic requests. Verify listener/process identity and startup options before stopping it.
- Current running process can differ from .env; restart is required for reliable configuration reload.
- Missing records or independent auth lookup failures can still yield null names; diagnose those read-only if necessary before declaring recovery.
