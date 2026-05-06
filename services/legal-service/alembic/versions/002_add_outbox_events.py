"""add outbox events table

Revision ID: 002
Revises: 001
Create Date: 2024-01-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'outbox_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False, index=True),
        sa.Column('topic', sa.String(200), nullable=False),
        sa.Column('payload', postgresql.JSON(), nullable=False),
        sa.Column('status', sa.String(20), default='pending', index=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('max_retries', sa.Integer(), default=5),
        sa.Column('created_at', sa.DateTime(), index=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.String(1000), nullable=True),
    )
    op.create_index('idx_outbox_status_created', 'outbox_events', ['status', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_outbox_status_created', table_name='outbox_events')
    op.drop_table('outbox_events')
