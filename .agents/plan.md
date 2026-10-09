# Plan: CRUD APIs for Departments, Majors, Sub-majors, and Students

## Ordered implementation steps

1. Establish a shared `JWT_SIGNING_KEY` environment configuration in
   auth-service and academic-service, configure Simple JWT to use it, and add
   a non-committed example entry to each relevant environment template.
2. Enable Django REST Framework and register the four existing academic apps.
   Add an academic-service JWT authentication class that verifies signature and
   expiry locally and exposes token claims without querying auth-service.
   Add a reusable permission class that permits all authenticated callers to
   read and permits only the integer role claim `1` to write.
3. Define models and integrity rules:
   `Department -> Major -> SubMajor`, and `Student -> Major/SubMajor`.
   Use protected foreign keys to prevent accidental destructive cascades.
4. Generate and review initial migrations for the four apps.
5. Add dedicated request and response DTO serializers (not direct model
   serialization), including validation that a supplied sub-major belongs to
   the student's supplied major.
6. Add viewsets and per-app URL modules; mount them in `config/urls.py` under
   `/api/` with plural resources:
   `departments`, `majors`, `sub-majors`, and `students`.
7. Add API tests for create/list/retrieve/update/delete, uniqueness and
   relationship validation, HTTP 404 behavior, missing/invalid JWT (`401`),
   read access for a valid non-1 role, and write denial for a valid JWT role
   other than `1` (`403`).
8. Document endpoint methods, payload fields, relationships, required bearer
   authentication and role `1`, plus error/status
   expectations.
9. Run `python manage.py check` and `python manage.py test` from
   `services/academic-services`; report any pre-existing failures separately.
10. Commit each manager app independently after its migration and tests pass;
    commit the academic-service API README after the app commits.

## Expected files to change

- `.agents/task.md`, `.agents/plan.md`
- `services/auth-service/config/settings.py`, `.env.example`
- `services/academic-services/config/settings.py`, `config/urls.py`
- `services/academic-services/.env.example`
- `services/academic-services` JWT authentication/permission module
- `services/academic-services/{DeparmentManager,MajorManager,SubMajorManager,StudentManager}/models.py`
- `services/academic-services/{DeparmentManager,MajorManager,SubMajorManager,StudentManager}/serializers.py`
- `services/academic-services/{DeparmentManager,MajorManager,SubMajorManager,StudentManager}/views.py`
- `services/academic-services/{DeparmentManager,MajorManager,SubMajorManager,StudentManager}/urls.py`
- `services/academic-services/{DeparmentManager,MajorManager,SubMajorManager,StudentManager}/tests.py`
- Initial migration files in each of those apps
- `services/academic-services/README.md` (and root `README.md` only if route
  documentation needs extending)

## Verification

- Execute Django system checks.
- Execute academic-service tests, including all four app test modules.
- Confirm response codes and validation behavior via the Django REST Framework
  test client.
- Confirm any signed access token can read, only `role: 1` can write, another
  valid role receives `403` on writes, and malformed/expired tokens receive
  `401`.

## Rollback

- Revert only the files listed above, including the initial migrations, and do
  not run migrations against shared/production databases until the change is
  reviewed.
