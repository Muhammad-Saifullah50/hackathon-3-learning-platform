"""create_code_sessions_table

Revision ID: a1b2c3d4e5f6
Revises: 83d6013dce9b
Create Date: 2026-05-10 15:30:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'a1b2c3d4e5f6'
down_revision = '83d6013dce9b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'code_sessions',
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('context_key', sa.String(255), nullable=False),
        sa.Column('code', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'context_key', name='pk_code_sessions'),
    )


def downgrade() -> None:
    op.drop_table('code_sessions')
