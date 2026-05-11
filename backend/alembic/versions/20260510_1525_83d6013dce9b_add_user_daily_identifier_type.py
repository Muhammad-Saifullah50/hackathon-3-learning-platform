"""add_user_daily_identifier_type

Revision ID: 83d6013dce9b
Revises: better_auth_tables
Create Date: 2026-05-10 15:25:41.088002

"""
import sqlalchemy as sa
from alembic import op

revision = '83d6013dce9b'
down_revision = 'better_auth_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ADD VALUE cannot run inside a transaction in PostgreSQL
    op.execute(sa.text("COMMIT"))
    op.execute(sa.text("ALTER TYPE identifiertype ADD VALUE IF NOT EXISTS 'user_daily'"))
    op.execute(sa.text("BEGIN"))
    op.execute(
        sa.text(
            "ALTER TABLE rate_limit_counters DROP CONSTRAINT IF EXISTS check_identifier_type"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE rate_limit_counters ADD CONSTRAINT check_identifier_type "
            "CHECK (identifier_type IN ('ip', 'email', 'user_daily'))"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TABLE rate_limit_counters DROP CONSTRAINT IF EXISTS check_identifier_type"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE rate_limit_counters ADD CONSTRAINT check_identifier_type "
            "CHECK (identifier_type IN ('ip', 'email'))"
        )
    )
