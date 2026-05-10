---
id: "0008"
title: Fix Better Auth camelCase Column Mismatch
stage: red
date: 2026-05-10
surface: agent
model: claude-sonnet-4-6
feature: 013-frontend-foundation
branch: 013-frontend-foundation
user: Muhammad
command: /sp.phr
labels: ["better-auth", "database", "alembic", "migration", "debugging", "camelCase", "schema"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/alembic/versions/20260509_create_better_auth_tables.py
  - frontend/src/lib/auth.ts
tests:
  - none
---

## Prompt

026-05-10T04:22:03.693Z ERROR [Better Auth]: Failed to create user error: column "emailVerified" of relation "user" does not exist
    at async POST (src/app/api/register-proxy/route.ts:52:27)
  ...
  code: '42703'
  routine: 'checkInsertTargets'

(Full error repeated 4 times across multiple registration attempts)

## Response snapshot

Root cause identified via systematic debugging: the Alembic migration `20260509_create_better_auth_tables.py` created all 4 Better Auth tables (`user`, `session`, `account`, `verification`) using snake_case column names (e.g., `email_verified`, `created_at`, `user_id`), but Better Auth expects camelCase by default (e.g., `emailVerified`, `createdAt`, `userId`). Fixed by: (1) updating the migration to use camelCase column names with proper quoting, (2) dropping the mismatched tables from Neon, (3) re-running the migration, and (4) fixing the raw SQL in `auth.ts`'s `attachFastApiTokenToLatestSession` to use camelCase column references.

## Outcome

- ✅ Impact: Better Auth signup now writes to correctly-named camelCase columns; `emailVerified`, `fastApiId`, `userId`, `fastApiToken`, `expiresAt`, `createdAt`, `updatedAt` etc. all exist in the DB and match Better Auth's expectations.
- 🧪 Tests: none
- 📁 Files: backend/alembic/versions/20260509_create_better_auth_tables.py, frontend/src/lib/auth.ts
- 🔁 Next prompts: Retry user registration in the browser to confirm 200 response; check `attachFastApiTokenToLatestSession` updates the session row correctly.
- 🧠 Reflection: Better Auth uses camelCase column names by default — any hand-written Alembic migration for Better Auth tables must quote camelCase identifiers (e.g., `"emailVerified"`) since PostgreSQL folds unquoted identifiers to lowercase.

## Evaluation notes (flywheel)

- Failure modes observed: Migration was written with snake_case column names that don't match Better Auth's default schema expectations.
- Graders run and results (PASS/FAIL): DB column verification via psycopg2 — PASS (all 4 tables now have camelCase columns).
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Add a comment to the migration file warning future developers that Better Auth column names must be camelCase-quoted.
