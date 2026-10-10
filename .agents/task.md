# Task: Manage student/lecturer identity and academic profiles together

Status: Awaiting explicit approval. Read-only schema/source inspection completed.

## Objective
Allow administrators to create, edit, view and delete a student/lecturer together with their associated Users record, including user-related fields in frontend add/edit popups.

## Architecture decision
Users already exists and is mapped in auth-service. Preserve the repository SOA ownership rule: auth-service alone maps/reads/writes Users; academic-service owns Students/Lecturers and coordinates identity operations through authenticated REST. Do not add a Users ORM model or foreign-key ORM join to academic-service. Existing academic models keep opaque user IDs. This plan achieves the requested record lifecycle without duplicate tables or cross-service ORM access.

## Schema evidence and ownership
- Users: UserId TEXT PK; LastName, FirstName, Gender, DateOfBirth, Password, Email, Phone, Role, Status, CreatedAt, UpdatedAt. Auth-service ownership.
- Students: StudentId TEXT PK referencing Users.UserId; MajorId, SpecializationId, AccumulatedCredits, GPA. Academic ownership.
- Lecturers: LecturerId TEXT PK referencing Users.UserId; FacultyId. Academic ownership.
- Registrations references Students; Topics references Lecturers and Users; AuditLogs references Users. Foreign keys use NO ACTION, so related business/audit data can prevent deletion.
- No schema changes, table creation, migrations or production database writes are planned. All mappings remain managed=False. Existing physical SQLite sharing does not grant cross-service table ownership.

## Scope
- Add versioned, service-authenticated auth-service contracts to create/read/update/delete only student/lecturer identities and batch-read safe profiles for admin academic lists.
- Add versioned composite student/lecturer endpoints in their existing academic apps; preserve legacy academic DTO/routes and public auth login/refresh/me contracts.
- Use Consul healthy auth-service discovery by default, bounded timeouts, bounded DTO/batch sizes, explicit errors, correlation IDs, throttling and a fail-fast dependency circuit. No automatic write retries or static fallback when discovery is enabled.
- Require service credentials plus administrator authorization on internal identity management calls; browser never receives service secrets. Prevent auth internal management routes from being exposed through Gateway.
- Frontend add/edit includes last_name, first_name, gender, date_of_birth, email, phone, status and password. Password required on create, optional/write-only on edit; blank edit password means unchanged. UserId remains tied to academic ID and immutable on edit. Role is server-assigned: student=3, lecturer=2. CreatedAt/UpdatedAt are server-generated and response-only.
- Return safe user DTO nested with academic DTO; never return stored passwords or password placeholders. Names become available for student/lecturer lists and explicit Search by code/name.
- Coordinate create/update/delete across REST with validation before changes, local transactions restricted to each service's owned tables, safe compensation where possible, and explicit incomplete-operation responses if a timeout/compensation failure leaves uncertain state.
- Successful delete means both the academic child row and identity row are deleted, not dropping either table. Reject referenced records rather than cascade-delete registrations/topics/audit logs; prevent deleting the caller, admins or mismatched-role identities.
- Update frontend forms/API types, backend/frontend tests, READMEs, environment examples and CI only where affected.

## Constraints
- Preserve fixed ports, service names, Gateway prefixes, database schema, unmanaged mappings and auth password/login policy.
- No importing/querying another service's ORM/private table. No distributed transaction or SQLite write transaction held open across an HTTP call.
- Do not silently adopt/delete an already-existing unrelated identity. Report conflicts safely.
- No blind write retry, logging passwords/tokens/personal payloads, exposing internal stack traces or returning successful deletes for partial work.
- Preserve prior frontend authentication/Gateway/academic work. Do not modify real .env secrets, dependency locks or generated database files.

## Acceptance criteria
- Add student/lecturer from frontend creates the matching user with correct role and academic child; successful login works through the unchanged auth contract using the new account.
- Edit popup preloads current safe identity fields and academic fields, supports identity+academic updates and optional password change without ever disclosing the previous password.
- Delete removes both records when unreferenced; linked business/audit records cause safe conflict feedback and remain intact. UI removes rows only on confirmed full success.
- Students/lecturers can be searched explicitly by code or returned name.
- Non-admin writes and unauthorized internal calls fail; arbitrary-user profile access is not exposed to browser clients.
- Validate duplicate IDs/email/phone and relationships against the actual schema, date format and DTO requirements. Full names use documented first/last-name fields. Gender/status allowed values are verified from existing contracts/schema before introducing enums.
- Tests cover create/edit/delete, identity/academic failures, partial outcomes/compensation, timeout uncertainty, duplicate requests, sensitive-field exclusion, authorization and existing auth/academic regressions.
- Relevant auth/academic Django check/test, Gateway tests/integration and frontend lint/test/build pass.

## Assumptions and risks
- The user intends deleting records, not dropping the Users/Students/Lecturers tables.
- Expanding auth-service and internal Gateway access policy is necessary to maintain the repository ownership rules; these changes are included for approval.
- REST cannot provide a single ACID transaction over both services. Compensation and explicit recovery errors reduce risk; process crashes or unresolved timeouts can require administrator reconciliation. This task does not introduce a broker, durable saga journal or schema changes.
- Existing NO ACTION references can prevent deleting Users even after child deletion; validate/compensate safely and do not erase audit history.
- Existing plaintext password policy is preserved for compatibility; no password hash migration is included.
- New service credentials must be supplied consistently via environment by the operator; never generate/commit real credentials in this task.
- Tests use isolated temporary SQLite/mock HTTP; no real account creation/deletion for verification.
