"""add faq knowledge base

Revision ID: i9j0k1l2m3n4
Revises: h8i6j7k8l9m0
Create Date: 2026-01-21 02:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import String, Integer, Text, DateTime, Boolean, Index


# revision identifiers, used by Alembic.
revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, None] = "h8i6j7k8l9m0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 检查表是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "faqs" not in tables:
        op.create_table(
            "faqs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("question", sa.String(length=500), nullable=False),
            sa.Column("answer", sa.Text(), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=True),
            sa.Column("tags", sa.String(length=500), nullable=True),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_faqs_question"), "faqs", ["question"], unique=False)
        op.create_index(op.f("ix_faqs_category"), "faqs", ["category"], unique=False)
        op.create_index(op.f("ix_faqs_priority"), "faqs", ["priority"], unique=False)
        op.create_index(op.f("ix_faqs_is_active"), "faqs", ["is_active"], unique=False)
        op.create_index(op.f("ix_faqs_created_at"), "faqs", ["created_at"], unique=False)
        op.create_index("idx_faqs_category_active", "faqs", ["category", "is_active"], unique=False)
        op.create_index("idx_faqs_priority_active", "faqs", ["priority", "is_active"], unique=False)


def downgrade() -> None:
    # 检查表是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "faqs" in tables:
        op.drop_index("idx_faqs_priority_active", table_name="faqs")
        op.drop_index("idx_faqs_category_active", table_name="faqs")
        op.drop_index(op.f("ix_faqs_created_at"), table_name="faqs")
        op.drop_index(op.f("ix_faqs_is_active"), table_name="faqs")
        op.drop_index(op.f("ix_faqs_priority"), table_name="faqs")
        op.drop_index(op.f("ix_faqs_category"), table_name="faqs")
        op.drop_index(op.f("ix_faqs_question"), table_name="faqs")
        op.drop_table("faqs")
