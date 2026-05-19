"""Add teacher dashboard tables

Revision ID: 20260518_teacher_dashboard
Revises: 20260518_mastery_snapshots
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "20260518_teacher_dashboard"
down_revision = "20260518_mastery_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. classes
    op.create_table(
        "classes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("teacher_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_class_teacher_id", "classes", ["teacher_id"])
    op.create_index("idx_class_created_at", "classes", ["created_at"])

    # 2. class_memberships
    op.create_table(
        "class_memberships",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("class_id", UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("invited_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("responded_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("class_id", "student_id", name="uq_membership_class_student"),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'declined')", name="ck_membership_status"),
    )
    op.create_index("idx_membership_class_id", "class_memberships", ["class_id"])
    op.create_index("idx_membership_student_id", "class_memberships", ["student_id"])
    op.create_index("idx_membership_status", "class_memberships", ["status"])
    op.create_index("idx_membership_created_at", "class_memberships", ["created_at"])

    # 3. teacher_generated_exercises
    op.create_table(
        "teacher_generated_exercises",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("target_module", sa.String(100), nullable=False),
        sa.Column("generation_prompt", sa.Text(), nullable=False),
        sa.Column("questions", JSONB(), nullable=False),
        sa.Column("created_by_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("difficulty IN ('beginner', 'intermediate', 'advanced')", name="ck_teacher_exercise_difficulty"),
    )
    op.create_index("idx_teacher_exercise_created_by", "teacher_generated_exercises", ["created_by_id"])
    op.create_index("idx_teacher_exercise_topic", "teacher_generated_exercises", ["topic"])
    op.create_index("idx_teacher_exercise_created_at", "teacher_generated_exercises", ["created_at"])

    # 4. class_exercises
    op.create_table(
        "class_exercises",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("class_id", UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", UUID(as_uuid=True), sa.ForeignKey("teacher_generated_exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_by_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("class_id", "exercise_id", name="uq_class_exercise"),
    )
    op.create_index("idx_class_exercise_class_id", "class_exercises", ["class_id"])
    op.create_index("idx_class_exercise_exercise_id", "class_exercises", ["exercise_id"])
    op.create_index("idx_class_exercise_created_at", "class_exercises", ["created_at"])

    # 5. class_exercise_submissions
    op.create_table(
        "class_exercise_submissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("class_exercise_id", UUID(as_uuid=True), sa.ForeignKey("class_exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(15), nullable=False, server_default="in_progress"),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("class_exercise_id", "student_id", name="uq_submission_class_exercise_student"),
        sa.CheckConstraint("status IN ('in_progress', 'submitted')", name="ck_submission_status"),
        sa.CheckConstraint("overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)", name="ck_submission_score"),
    )
    op.create_index("idx_submission_class_exercise_id", "class_exercise_submissions", ["class_exercise_id"])
    op.create_index("idx_submission_student_id", "class_exercise_submissions", ["student_id"])
    op.create_index("idx_submission_status", "class_exercise_submissions", ["status"])
    op.create_index("idx_submission_created_at", "class_exercise_submissions", ["created_at"])

    # 6. question_reviews
    op.create_table(
        "question_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("class_exercise_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_index", sa.Integer(), nullable=False),
        sa.Column("student_code", sa.Text(), nullable=False),
        sa.Column("ai_review", sa.Text(), nullable=False),
        sa.Column("grade", sa.Float(), nullable=False),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("submission_id", "question_index", name="uq_question_review"),
        sa.CheckConstraint("grade >= 0 AND grade <= 100", name="ck_review_grade"),
        sa.CheckConstraint("question_index >= 0", name="ck_review_question_index"),
    )
    op.create_index("idx_question_review_submission_id", "question_reviews", ["submission_id"])
    op.create_index("idx_question_review_created_at", "question_reviews", ["created_at"])

    # 7. teacher_notifications
    op.create_table(
        "teacher_notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("teacher_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("class_exercise_submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("notification_type", sa.String(50), nullable=False, server_default="exercise_submitted"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_teacher_notif_teacher_id", "teacher_notifications", ["teacher_id"])
    op.create_index("idx_teacher_notif_is_read", "teacher_notifications", ["is_read"])
    op.create_index("idx_teacher_notif_created_at", "teacher_notifications", ["created_at"])


def downgrade() -> None:
    op.drop_table("teacher_notifications")
    op.drop_table("question_reviews")
    op.drop_table("class_exercise_submissions")
    op.drop_table("class_exercises")
    op.drop_table("teacher_generated_exercises")
    op.drop_table("class_memberships")
    op.drop_table("classes")
