"""add channels table

Revision ID: q2r3s4t5u6v7
Revises: p1q2r3s4t5u6
Create Date: 2026-02-03 13:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "q2r3s4t5u6v7"
down_revision: Union[str, None] = "p1q2r3s4t5u6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 channels 表
    op.create_table(
        "channels",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, comment="渠道名称"),
        sa.Column("code", sa.String(length=50), nullable=False, comment="渠道代码，唯一标识"),
        sa.Column("description", sa.Text(), nullable=True, comment="渠道描述"),
        sa.Column("url", sa.String(length=500), nullable=True, comment="渠道链接"),
        sa.Column("type", sa.String(length=20), nullable=False, server_default="other", comment="渠道类型: weixin/douyin/xiaohongshu/zhihu/bilibili/website/other"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active", comment="状态: active/inactive"),
        sa.Column("visit_count", sa.Integer(), nullable=False, server_default="0", comment="访问数"),
        sa.Column("register_count", sa.Integer(), nullable=False, server_default="0", comment="注册数"),
        sa.Column("activation_count", sa.Integer(), nullable=False, server_default="0", comment="激活数"),
        sa.Column("payment_count", sa.Integer(), nullable=False, server_default="0", comment="支付/转化数"),
        sa.Column("total_revenue", sa.Integer(), nullable=False, server_default="0", comment="总收入(分)"),
        sa.Column("landing_config", sa.Text(), nullable=True, comment="落地页配置(JSON格式)"),
        sa.Column("offer_config", sa.Text(), nullable=True, comment="优惠配置(JSON格式)"),
        sa.Column("tracking_config", sa.Text(), nullable=True, comment="追踪配置(JSON格式)"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    
    # 创建索引
    op.create_index(
        "ix_channels_code",
        "channels",
        ["code"],
        unique=False,
    )
    op.create_index(
        "ix_channels_status",
        "channels",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_channels_type",
        "channels",
        ["type"],
        unique=False,
    )


def downgrade() -> None:
    # 删除索引
    op.drop_index(
        "ix_channels_type",
        table_name="channels",
    )
    op.drop_index(
        "ix_channels_status",
        table_name="channels",
    )
    op.drop_index(
        "ix_channels_code",
        table_name="channels",
    )
    
    # 删除表
    op.drop_table("channels")