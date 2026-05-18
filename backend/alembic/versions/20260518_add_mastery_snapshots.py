"""Add mastery_snapshots table

Revision ID: 20260518_mastery_snapshots
Revises: 20260517_quiz_sessions
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260518_mastery_snapshots"
down_revision = "20260517_quiz_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mastery_snapshots",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "module_id",
            sa.Integer(),
            sa.ForeignKey("modules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_mastery_snapshots_user_recorded",
        "mastery_snapshots",
        ["user_id", sa.text("recorded_at DESC")],
    )
    op.create_index(
        "idx_mastery_snapshots_user_module",
        "mastery_snapshots",
        ["user_id", "module_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_mastery_snapshots_user_module", table_name="mastery_snapshots")
    op.drop_index("idx_mastery_snapshots_user_recorded", table_name="mastery_snapshots")
    op.drop_table("mastery_snapshots")
