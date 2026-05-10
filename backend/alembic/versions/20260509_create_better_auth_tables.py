"""create_better_auth_tables

Revision ID: better_auth_tables
Revises: create_agent_tables
Create Date: 2026-05-09

Adds the four tables Better Auth requires for session management:
    - "user"        (Better Auth user record, separate from FastAPI users.users)
    - "session"     (Better Auth session, contains FastAPI JWT for backend calls)
    - "account"     (credential provider linkage)
    - "verification" (email verification + password reset tokens)

`user` and `session` are Postgres reserved words, so we quote them explicitly
via raw DDL. The tables are owned by the Next.js / Better Auth layer; FastAPI's
existing `users` table remains the authoritative credential store and is
referenced via `user.fastApiId`.

Column names use camelCase to match Better Auth's default expectations.
"""

from alembic import op

revision = "better_auth_tables"
down_revision = "create_agent_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE "user" (
            id              text PRIMARY KEY,
            name            text NOT NULL,
            email           text NOT NULL UNIQUE,
            "emailVerified" boolean NOT NULL DEFAULT false,
            image           text,
            role            text NOT NULL DEFAULT 'student',
            "fastApiId"     text,
            "createdAt"     timestamptz NOT NULL DEFAULT NOW(),
            "updatedAt"     timestamptz NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute('CREATE INDEX idx_better_auth_user_email ON "user" (email);')
    op.execute('CREATE INDEX idx_better_auth_user_fast_api_id ON "user" ("fastApiId");')

    op.execute(
        """
        CREATE TABLE "session" (
            id              text PRIMARY KEY,
            "expiresAt"     timestamptz NOT NULL,
            token           text NOT NULL UNIQUE,
            "userId"        text NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            "ipAddress"     text,
            "userAgent"     text,
            "fastApiToken"  text,
            "createdAt"     timestamptz NOT NULL DEFAULT NOW(),
            "updatedAt"     timestamptz NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute('CREATE INDEX idx_better_auth_session_user_id ON "session" ("userId");')
    op.execute('CREATE INDEX idx_better_auth_session_token ON "session" (token);')

    op.execute(
        """
        CREATE TABLE "account" (
            id                          text PRIMARY KEY,
            "accountId"                 text NOT NULL,
            "providerId"                text NOT NULL,
            "userId"                    text NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            "accessToken"               text,
            "refreshToken"              text,
            "idToken"                   text,
            "accessTokenExpiresAt"      timestamptz,
            "refreshTokenExpiresAt"     timestamptz,
            scope                       text,
            password                    text,
            "createdAt"                 timestamptz NOT NULL DEFAULT NOW(),
            "updatedAt"                 timestamptz NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute('CREATE INDEX idx_better_auth_account_user_id ON "account" ("userId");')

    op.execute(
        """
        CREATE TABLE "verification" (
            id           text PRIMARY KEY,
            identifier   text NOT NULL,
            value        text NOT NULL,
            "expiresAt"  timestamptz NOT NULL,
            "createdAt"  timestamptz NOT NULL DEFAULT NOW(),
            "updatedAt"  timestamptz NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute(
        'CREATE INDEX idx_better_auth_verification_identifier ON "verification" (identifier);'
    )


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS "verification" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "account" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "session" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "user" CASCADE;')
