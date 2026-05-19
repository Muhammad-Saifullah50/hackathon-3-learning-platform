"""Add classes and class_memberships tables (F019).

Revision ID: 20260519_classes
Revises: 20260518_mastery_snapshots
Create Date: 2026-05-19

Note: these tables were pre-created in the DB before this migration was written.
Using IF NOT EXISTS so this migration is idempotent.

Schema (actual):
  classes: id, teacher_id, name, created_at, updated_at
  class_memberships: id, class_id, student_id, status, invited_at, responded_at, created_at, updated_at
"""

from alembic import op

revision = "20260519_classes"
down_revision = "20260518_mastery_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id UUID NOT NULL,
            name VARCHAR(100) NOT NULL,
            teacher_id UUID NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(teacher_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_classes_teacher_id ON classes (teacher_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS class_memberships (
            id UUID NOT NULL,
            class_id UUID NOT NULL,
            student_id UUID NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            invited_at TIMESTAMP WITH TIME ZONE,
            responded_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(class_id) REFERENCES classes (id) ON DELETE CASCADE,
            FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE,
            CONSTRAINT uq_class_membership UNIQUE (class_id, student_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_class_memberships_class_id ON class_memberships (class_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_class_memberships_student_id ON class_memberships (student_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS class_memberships")
    op.execute("DROP TABLE IF EXISTS classes")
