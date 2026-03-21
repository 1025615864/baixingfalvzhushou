"""add_user_onboarding_table

Revision ID: u3v4w5x6y7z8
Revises: t2u3v4w5x6y7
Create Date: 2026-02-17 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "u3v4w5x6y7z8"
down_revision: Union[str, None] = "t2u3v4w5x6y7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 用户引导状态表
    op.create_table(
        "user_onboarding",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.Integer(), server_default="0", nullable=False),
        sa.Column("role_id", sa.String(length=50), nullable=True),
        sa.Column("role_selected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("matched_needs", sa.JSON(), nullable=True),
        sa.Column("needs_matched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_demos", sa.JSON(), nullable=True),
        sa.Column("demo_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_onboarding_user_id"),
    )
    op.create_index("ix_user_onboarding_user_id", "user_onboarding", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_onboarding_user_id", table_name="user_onboarding")
    op.drop_table("user_onboarding")