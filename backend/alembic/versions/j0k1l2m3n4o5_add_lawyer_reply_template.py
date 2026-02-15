"""add lawyer reply template

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-01-21 02:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision: str = 'j0k1l2m3n4o5'
down_revision: Union[str, None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建律师快捷回复模板表
    op.create_table(
        'lawyer_reply_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('use_count', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
        sa.ForeignKeyConstraint(['lawyer_id'], ['lawyers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lawyer_reply_templates_category'), 'lawyer_reply_templates', ['category'], unique=False)
    op.create_index(op.f('ix_lawyer_reply_templates_is_active'), 'lawyer_reply_templates', ['is_active'], unique=False)
    op.create_index(op.f('ix_lawyer_reply_templates_lawyer_id'), 'lawyer_reply_templates', ['lawyer_id'], unique=False)


def downgrade() -> None:
    # 删除律师快捷回复模板表
    op.drop_index(op.f('ix_lawyer_reply_templates_lawyer_id'), table_name='lawyer_reply_templates')
    op.drop_index(op.f('ix_lawyer_reply_templates_is_active'), table_name='lawyer_reply_templates')
    op.drop_index(op.f('ix_lawyer_reply_templates_category'), table_name='lawyer_reply_templates')
    op.drop_table('lawyer_reply_templates')
