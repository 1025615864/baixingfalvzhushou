"""添加refresh_tokens表支持Token轮换

Revision ID: xxxx_add_refresh_tokens
Revises: n3o4p5q6r7s8
Create Date: 2026-01-31 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, sqlite

# revision identifiers, used by Alembic.
revision: str = 'xxxx_add_refresh_tokens'
down_revision: Union[str, None] = 'n3o4p5q6r7s8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建refresh_tokens表"""
    
    # 根据数据库类型选择适当的数据类型
    dialect = op.get_context().dialect.name
    
    if dialect == 'postgresql':
        datetime_type = sa.DateTime(timezone=True)
    else:
        datetime_type = sa.DateTime()
    
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_jti', sa.String(length=64), nullable=False),
        sa.Column('token_family', sa.String(length=64), nullable=False),
        sa.Column('issued_at', datetime_type, nullable=False),
        sa.Column('expires_at', datetime_type, nullable=False),
        sa.Column('rotated_at', datetime_type, nullable=True),
        sa.Column('rotation_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('revoked_at', datetime_type, nullable=True),
        sa.Column('revoked_reason', sa.String(length=50), nullable=True),
        sa.Column('device_info', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        
        # 主键约束
        sa.PrimaryKeyConstraint('id'),
        
        # 唯一约束
        sa.UniqueConstraint('token_jti', name='uq_refresh_tokens_jti'),
    )
    
    # 创建索引
    op.create_index(
        'ix_refresh_tokens_user_id',
        'refresh_tokens',
        ['user_id']
    )
    op.create_index(
        'ix_refresh_tokens_token_jti',
        'refresh_tokens',
        ['token_jti']
    )
    op.create_index(
        'ix_refresh_tokens_token_family',
        'refresh_tokens',
        ['token_family']
    )
    op.create_index(
        'ix_refresh_tokens_expires_at',
        'refresh_tokens',
        ['expires_at']
    )
    op.create_index(
        'ix_refresh_tokens_is_revoked',
        'refresh_tokens',
        ['is_revoked']
    )
    op.create_index(
        'ix_refresh_tokens_user_revoked',
        'refresh_tokens',
        ['user_id', 'is_revoked']
    )


def downgrade() -> None:
    """删除refresh_tokens表"""
    op.drop_index('ix_refresh_tokens_user_revoked', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_is_revoked', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_expires_at', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token_family', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_token_jti', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')