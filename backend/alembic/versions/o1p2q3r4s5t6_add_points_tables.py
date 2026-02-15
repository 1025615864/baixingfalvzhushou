"""add points tables

Revision ID: o1p2q3r4s5t6
Revises: a1b2c3d4e5f6, g8h9i0j1k2l3
Create Date: 2026-01-21 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "o1p2q3r4s5t6"
down_revision: Union[str, tuple[str, str], None] = ("a1b2c3d4e5f6", "g8h9i0j1k2l3")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "points_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_earned", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_spent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("continuous_signin_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_signin_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_points_users_user_id"),
    )
    op.create_index("ix_points_users_user_id", "points_users", ["user_id"], unique=True)

    op.create_table(
        "points_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("balance_before", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["points_users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_points_history_user_id", "points_history", ["user_id"], unique=False)
    op.create_index("ix_points_history_action", "points_history", ["action"], unique=False)
    op.create_index("ix_points_history_created_at", "points_history", ["created_at"], unique=False)

    op.create_table(
        "points_daily_counts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("date", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["points_users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_points_daily_counts_user_id", "points_daily_counts", ["user_id"], unique=False)
    op.create_index("ix_points_daily_counts_date", "points_daily_counts", ["date"], unique=False)
    op.create_index(
        "ix_points_daily_counts_user_date",
        "points_daily_counts",
        ["user_id", "date"],
        unique=False,
    )

    op.create_table(
        "points_products",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("points_required", sa.Integer(), nullable=False),
        sa.Column("product_type", sa.String(length=50), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("stock", sa.Integer(), server_default="-1", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_points_products_product_type", "points_products", ["product_type"], unique=False)

    op.create_table(
        "points_exchange_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(length=50), nullable=False),
        sa.Column("product_name", sa.String(length=100), nullable=False),
        sa.Column("points_spent", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("shipping_info", sa.JSON(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["points_products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_no", name="uq_points_exchange_orders_order_no"),
    )
    op.create_index("ix_points_exchange_orders_order_no", "points_exchange_orders", ["order_no"], unique=True)
    op.create_index("ix_points_exchange_orders_user_id", "points_exchange_orders", ["user_id"], unique=False)
    op.create_index("ix_points_exchange_orders_product_id", "points_exchange_orders", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_points_exchange_orders_product_id", table_name="points_exchange_orders")
    op.drop_index("ix_points_exchange_orders_user_id", table_name="points_exchange_orders")
    op.drop_index("ix_points_exchange_orders_order_no", table_name="points_exchange_orders")
    op.drop_table("points_exchange_orders")

    op.drop_index("ix_points_products_product_type", table_name="points_products")
    op.drop_table("points_products")

    op.drop_index("ix_points_daily_counts_user_date", table_name="points_daily_counts")
    op.drop_index("ix_points_daily_counts_date", table_name="points_daily_counts")
    op.drop_index("ix_points_daily_counts_user_id", table_name="points_daily_counts")
    op.drop_table("points_daily_counts")

    op.drop_index("ix_points_history_created_at", table_name="points_history")
    op.drop_index("ix_points_history_action", table_name="points_history")
    op.drop_index("ix_points_history_user_id", table_name="points_history")
    op.drop_table("points_history")

    op.drop_index("ix_points_users_user_id", table_name="points_users")
    op.drop_table("points_users")
