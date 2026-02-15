"""add cross domain tables

Revision ID: p1q2r3s4t5u6
Revises: o1p2q3r4s5t6
Create Date: 2026-02-03 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "p1q2r3s4t5u6"
down_revision: Union[str, None] = "o1p2q3r4s5t6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 cross_domain_domains 表
    op.create_table(
        "cross_domain_domains",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("verification_code", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("verification_code"),
    )
    
    # 创建索引
    op.create_index(
        "ix_cross_domain_domains_domain",
        "cross_domain_domains",
        ["domain"],
        unique=False,
    )
    op.create_index(
        "ix_cross_domain_domains_status",
        "cross_domain_domains",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_cross_domain_domains_user_id",
        "cross_domain_domains",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    # 删除索引
    op.drop_index(
        "ix_cross_domain_domains_user_id",
        table_name="cross_domain_domains",
    )
    op.drop_index(
        "ix_cross_domain_domains_status",
        table_name="cross_domain_domains",
    )
    op.drop_index(
        "ix_cross_domain_domains_domain",
        table_name="cross_domain_domains",
    )
    
    # 删除表
    op.drop_table("cross_domain_domains")