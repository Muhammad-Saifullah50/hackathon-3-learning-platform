"""Create quiz_sessions table

Revision ID: 20260517_quiz_sessions
Revises: b2c3d4e5f6a7
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260517_quiz_sessions"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None

VALID_SLUGS = "('basics','control_flow','data_structures','functions','oop','files','errors','libraries')"
VALID_STATUS = "('generated','in_progress','completed')"


def upgrade() -> None:
    op.create_table(
        "quiz_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chat_session_id", UUID(as_uuid=True), sa.ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_slug", sa.String(50), nullable=False),
        sa.Column("topic_label", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="generated"),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("questions", JSONB, nullable=False),
        sa.Column("student_answers", JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("grades", JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_check_constraint("ck_quiz_status", "quiz_sessions", f"status IN {VALID_STATUS}")
    op.create_check_constraint("ck_quiz_score", "quiz_sessions", "score IS NULL OR (score >= 0 AND score <= 100)")
    op.create_check_constraint("ck_quiz_module_slug", "quiz_sessions", f"module_slug IN {VALID_SLUGS}")

    op.create_index("idx_quiz_sessions_student_id",   "quiz_sessions", ["student_id"])
    op.create_index("idx_quiz_sessions_chat_session",  "quiz_sessions", ["chat_session_id"])
    op.create_index("idx_quiz_sessions_status",        "quiz_sessions", ["status"])
    op.create_index("idx_quiz_sessions_module_slug",   "quiz_sessions", ["module_slug"])
    op.create_index("idx_quiz_sessions_created_at",    "quiz_sessions", ["created_at"])


def downgrade() -> None:
    op.drop_table("quiz_sessions")
