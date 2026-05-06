"""add moderation queue

Revision ID: 004
Revises: 003
Create Date: 2024-01-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'moderation_queue',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('content_type', sa.String(length=20), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('content_preview', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('report_reason', sa.String(length=500), nullable=True),
        sa.Column('reporter_id', sa.Integer(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_analysis', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('review_decision', sa.String(length=20), nullable=True),
        sa.Column('review_reason', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_moderation_queue_priority_status', 'moderation_queue', ['priority', 'status'])
    op.create_index('idx_moderation_queue_content', 'moderation_queue', ['content_type', 'content_id'])


def downgrade() -> None:
    op.drop_index('idx_moderation_queue_content', table_name='moderation_queue')
    op.drop_index('idx_moderation_queue_priority_status', table_name='moderation_queue')
    op.drop_table('moderation_queue')
