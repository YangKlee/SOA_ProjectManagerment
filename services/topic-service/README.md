# Topic Service

`topic-service` owns the existing `Topics` table in the shared project
database. It uses database-first mapping (`managed = False`) and never creates
or migrates that schema.

Run on port `8004` after setting the same `JWT_SIGNING_KEY` as auth-service.

- `GET /health/` is public.
- `GET /api/topics/` requires a valid JWT.
- Topic writes require JWT `role: 1`.
