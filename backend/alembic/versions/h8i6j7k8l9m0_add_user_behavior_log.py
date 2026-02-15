"""add user behavior log

Revision ID: h8i6j7k8l9m0
Revises: g7h5i6j7k8l9
Create Date: 2026-01-21 02:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, Integer, Text, DateTime, Index


# revision identifiers, used by Alembic.
revision: str = "h8i6j7k8l9m0"
down_revision: Union[str, None] = "g7h5i6j7k8l9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 检查表是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "user_behavior_logs" not in tables:
        op.create_table(
            "user_behavior_logs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=50), nullable=False),
            sa.Column("resource_type", sa.String(length=50), nullable=True),
            sa.Column("resource_id", sa.Integer(), nullable=True),
            sa.Column("metadata", sa.Text(), nullable=True),
            sa.Column("ip_address", sa.String(length=50), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("referrer", sa.String(length=500), nullable=True),
            sa.Column("session_id", sa.String(length=100), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_user_behavior_logs_user_id"), "user_behavior_logs", ["user_id"], unique=False)
        op.create_index(op.f("ix_user_behavior_logs_action"), "user_behavior_logs", ["action"], unique=False)
        op.create_index(op.f("ix_user_behavior_logs_resource_type"), "user_behavior_logs", ["resource_type"], unique=False)
        op.create_index(op.f("ix_user_behavior_logs_session_id"), "user_behavior_logs", ["session_id"], unique=False)
        op.create_index(op.f("ix_user_behavior_logs_created_at"), "user_behavior_logs", ["created_at"], unique=False)
        op.create_index("idx_user_behavior_logs_user_action", "user_behavior_logs", ["user_id", "action"], unique=False)
        op.create_index("idx_user_behavior_logs_resource", "user_behavior_logs", ["resource_type", "resource_id"], unique=False)


def downgrade() -> None:
    # 检查表是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "user_behavior_logs" in tables:
        op.drop_index("idx_user_behavior_logs_resource", table_name="user_behavior_logs")
        op.drop_index("idx_user_behavior_logs_user_action", table_name="user_behavior_logs")
        op.drop_index(op.f("ix_user_behavior_logs_created_at"), table_name="user_behavior_logs")
        op.drop_index(op.f("ix_user_behavior_logs_session_id"), table_name="user_behavior_logs")
        op.drop_index(op.f("ix_user_behavior_logs_resource_type"), table_name="user_behavior_logs")
        op.drop_index(op.f("ix_user_behavior_logs_action"), table_name="user_behavior_logs")
        op.drop_index(op.f("ix_user_behavior_logs_user_id"), table_name="user_behavior_logs")
        op.drop_table("user_behavior_logs")
