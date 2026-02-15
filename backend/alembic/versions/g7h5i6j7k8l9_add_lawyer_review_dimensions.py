"""add lawyer review dimensions

Revision ID: g7h5i6j7k8l9
Revises: f6g4h5i6j7k8
Create Date: 2026-01-21 01:44:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "g7h5i6j7k8l9"
down_revision: Union[str, None] = "f6g4h5i6j7k8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 检查表是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "lawyer_reviews" in tables:
        # 检查列是否已存在
        columns = [col["name"] for col in inspector.get_columns("lawyer_reviews")]

        if "professionalism" not in columns:
            op.add_column(
                "lawyer_reviews",
                sa.Column("professionalism", sa.Integer(), nullable=True)
            )

        if "responsiveness" not in columns:
            op.add_column(
                "lawyer_reviews",
                sa.Column("responsiveness", sa.Integer(), nullable=True)
            )

        if "attitude" not in columns:
            op.add_column(
                "lawyer_reviews",
                sa.Column("attitude", sa.Integer(), nullable=True)
            )

        if "tags" not in columns:
            op.add_column(
                "lawyer_reviews",
                sa.Column("tags", sa.String(length=500), nullable=True)
            )


def downgrade() -> None:
    # 检查表是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "lawyer_reviews" in tables:
        # 检查列是否存在
        columns = [col["name"] for col in inspector.get_columns("lawyer_reviews")]

        if "professionalism" in columns:
            op.drop_column("lawyer_reviews", "professionalism")

        if "responsiveness" in columns:
            op.drop_column("lawyer_reviews", "responsiveness")

        if "attitude" in columns:
            op.drop_column("lawyer_reviews", "attitude")

        if "tags" in columns:
            op.drop_column("lawyer_reviews", "tags")
