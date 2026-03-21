"""添加通知已读时间字段

Revision ID: add_notification_read_at
Revises: 
Create Date: 2026-02-17 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_notification_read_at'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 read_at 字段到 notifications 表"""
    # 检查列是否已存在
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'read_at'")
    ).fetchone()
    
    if not result:
        op.add_column(
            'notifications',
            sa.Column('read_at', sa.DateTime(timezone=True), nullable=True)
        )
        # 创建索引优化查询
        op.create_index(
            'ix_notifications_read_at',
            'notifications',
            ['read_at'],
            postgresql_using='btree'
        )


def downgrade() -> None:
    """移除 read_at 字段"""
    op.drop_index('ix_notifications_read_at', table_name='notifications')
    op.drop_column('notifications', 'read_at')