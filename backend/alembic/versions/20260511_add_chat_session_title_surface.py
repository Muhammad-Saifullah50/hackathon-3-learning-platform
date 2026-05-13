"""add_chat_session_title_surface

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-11 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('agent_sessions', sa.Column('title', sa.Text(), nullable=True))
    op.add_column('agent_sessions', sa.Column('surface', sa.String(20), nullable=True))
    op.create_check_constraint(
        'check_session_surface',
        'agent_sessions',
        "surface IN ('standalone', 'embedded') OR surface IS NULL",
    )
    op.create_index(
        'idx_agent_session_user_updated',
        'agent_sessions',
        ['user_id', sa.text('updated_at DESC')],
    )


def downgrade() -> None:
    op.drop_index('idx_agent_session_user_updated', table_name='agent_sessions')
    op.drop_constraint('check_session_surface', 'agent_sessions', type_='check')
    op.drop_column('agent_sessions', 'surface')
    op.drop_column('agent_sessions', 'title')
