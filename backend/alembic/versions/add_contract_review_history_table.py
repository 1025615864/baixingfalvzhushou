"""add contract review history table

Revision ID: add_contract_review_history
Revises: 
Create Date: 2026-01-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_contract_review_history'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Clean up any existing objects from failed migrations
    op.execute("DROP INDEX IF EXISTS ix_contract_review_history_user_id")
    op.execute("DROP INDEX IF EXISTS ix_contract_review_history_risk_level")
    op.execute("DROP INDEX IF EXISTS ix_contract_review_history_request_id")
    op.execute("DROP INDEX IF EXISTS ix_contract_review_history_created_at")
    op.execute("DROP TABLE IF EXISTS contract_review_history")
    
    # Create contract_review_history table
    # Using sa.String() for risk_level to avoid enum type creation issues
    op.create_table(
        'contract_review_history',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('contract_type', sa.String(100), nullable=True),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('text_chars', sa.Integer(), default=0),
        sa.Column('text_preview', sa.Text()),
        sa.Column('risk_level', sa.String(10), default='low', index=True),
        sa.Column('risk_count', sa.Integer(), default=0),
        sa.Column('report_json', sa.JSON(), nullable=True),
        sa.Column('report_markdown', sa.Text()),
        sa.Column('request_id', sa.String(64), index=True),
        sa.Column('focus', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), index=True),
    )
    
    # Indexes are automatically created by SQLAlchemy when index=True is set on columns
    # No need to manually create them


def downgrade() -> None:
    # Drop indexes if they exist
    op.execute("DROP INDEX IF EXISTS ix_contract_review_history_created_at")
    op.execute("DROP INDEX IF EXISTS ix_contract_review_history_request_id")
    op.execute("DROP INDEX IF EXISTS ix_contract_review_history_risk_level")
    op.execute("DROP INDEX IF EXISTS ix_contract_review_history_user_id")
    
    # Drop table if it exists
    op.execute("DROP TABLE IF EXISTS contract_review_history")