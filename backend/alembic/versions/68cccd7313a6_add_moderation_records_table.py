"""add_moderation_records_table

Revision ID: 68cccd7313a6
Revises: b647f3d851d9
Create Date: 2026-01-29 11:25:03.094370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68cccd7313a6'
down_revision: Union[str, None] = 'b647f3d851d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'moderation_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('decision', sa.String(length=20), nullable=False),
        sa.Column('matched_keywords', sa.Text(), nullable=True),
        sa.Column('ai_review_result', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('moderated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_moderation_content_hash', 'moderation_records', ['content_hash'], unique=False)
    op.create_index('idx_moderation_decision', 'moderation_records', ['decision'], unique=False)
    op.create_index('idx_moderation_created_at', 'moderation_records', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_moderation_created_at', table_name='moderation_records')
    op.drop_index('idx_moderation_decision', table_name='moderation_records')
    op.drop_index('idx_moderation_content_hash', table_name='moderation_records')
    op.drop_table('moderation_records')
