"""add lawyer promotion link

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-01-21 03:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'l2m3n4o5p6q7'
down_revision: Union[str, None] = 'k1l2m3n4o5p6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建律师推广链接表
    op.create_table(
        'lawyer_promotion_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('link_code', sa.String(length=50), nullable=False),
        sa.Column('link_name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('click_count', sa.Integer(), default=0, nullable=False),
        sa.Column('consultation_count', sa.Integer(), default=0, nullable=False),
        sa.Column('conversion_count', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['lawyer_id'], ['lawyers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('link_code'),
    )
    op.create_index(op.f('ix_lawyer_promotion_links_lawyer_id'), 'lawyer_promotion_links', ['lawyer_id'], unique=False)
    op.create_index(op.f('ix_lawyer_promotion_links_link_code'), 'lawyer_promotion_links', ['link_code'], unique=True)
    op.create_index(op.f('ix_lawyer_promotion_links_is_active'), 'lawyer_promotion_links', ['is_active'], unique=False)


def downgrade() -> None:
    # 删除律师推广链接表
    op.drop_index(op.f('ix_lawyer_promotion_links_is_active'), table_name='lawyer_promotion_links')
    op.drop_index(op.f('ix_lawyer_promotion_links_link_code'), table_name='lawyer_promotion_links')
    op.drop_index(op.f('ix_lawyer_promotion_links_lawyer_id'), table_name='lawyer_promotion_links')
    op.drop_table('lawyer_promotion_links')
