"""add lawyer schedule table

Revision ID: f6g4h5i6j7k8
Revises: e5f3g4h5i6j7
Create Date: 2026-01-21 01:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f6g4h5i6j7k8"
down_revision: Union[str, None] = "e5f3g4h5i6j7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 检查表是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "lawyer_schedules" not in tables:
        op.create_table(
            "lawyer_schedules",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("lawyer_id", sa.Integer(), nullable=False),
            sa.Column("date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("start_time", sa.String(length=10), nullable=False),
            sa.Column("end_time", sa.String(length=10), nullable=False),
            sa.Column("is_available", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("consultation_id", sa.Integer(), nullable=True),
            sa.Column("note", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["lawyer_id"], ["lawyers.id"]),
            sa.ForeignKeyConstraint(["consultation_id"], ["lawyer_consultations.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("lawyer_id", "date", "start_time", name="uq_lawyer_schedule_time"),
        )
        op.create_index(op.f("ix_lawyer_schedules_lawyer_id"), "lawyer_schedules", ["lawyer_id"], unique=False)
        op.create_index(op.f("ix_lawyer_schedules_date"), "lawyer_schedules", ["date"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lawyer_schedules_date"), table_name="lawyer_schedules")
    op.drop_index(op.f("ix_lawyer_schedules_lawyer_id"), table_name="lawyer_schedules")
    op.drop_table("lawyer_schedules")
