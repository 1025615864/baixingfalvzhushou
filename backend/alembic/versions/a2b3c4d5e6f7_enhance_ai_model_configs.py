"""enhance_ai_model_configs

Revision ID: a2b3c4d5e6f7
Revises: z9y8x7w6v5u4
Create Date: 2026-02-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'z9y8x7w6v5u4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to ai_model_configs table
    with op.batch_alter_table('ai_model_configs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('provider', sa.String(length=50), server_default='openai', nullable=False))
        batch_op.add_column(sa.Column('priority', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('is_primary', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('call_count', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('error_count', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('health_status', sa.String(length=20), server_default='unknown', nullable=False))
        batch_op.add_column(sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('health_check_message', sa.String(length=500), nullable=True))
        batch_op.create_index('ix_ai_model_configs_provider', ['provider'], unique=False)


def downgrade() -> None:
    # Drop columns from ai_model_configs table
    with op.batch_alter_table('ai_model_configs', schema=None) as batch_op:
        batch_op.drop_index('ix_ai_model_configs_provider')
        batch_op.drop_column('health_check_message')
        batch_op.drop_column('last_health_check')
        batch_op.drop_column('health_status')
        batch_op.drop_column('last_used_at')
        batch_op.drop_column('error_count')
        batch_op.drop_column('call_count')
        batch_op.drop_column('is_primary')
        batch_op.drop_column('priority')
        batch_op.drop_column('provider')
