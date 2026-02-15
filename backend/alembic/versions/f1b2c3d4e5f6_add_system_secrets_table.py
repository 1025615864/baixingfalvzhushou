from __future__ import annotations

from typing import Iterable

from alembic import op
import sqlalchemy as sa


revision: str = "f1b2c3d4e5f6"
down_revision: str | None = "d4f2c9a31b10"
branch_labels: str | None = None
depends_on: str | None = None


def _get_table_names(insp: sa.Inspector) -> set[str]:
    try:
        names = insp.get_table_names()
    except Exception:
        return set()
    return {str(n) for n in names if n}


def _get_index_names(insp: sa.Inspector, table_name: str) -> set[str]:
    try:
        indexes = insp.get_indexes(table_name)
    except Exception:
        return set()
    return {str(ix.get("name") or "") for ix in indexes if ix.get("name")}


def _ensure_indexes(table_name: str, index_specs: Iterable[tuple[str, list[str], bool]]) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = _get_index_names(insp, table_name)

    for name, cols, unique in index_specs:
        if name in existing:
            continue
        op.create_index(name, table_name, cols, unique=bool(unique))


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = _get_table_names(insp)

    if "system_secrets" not in tables:
        op.create_table(
            "system_secrets",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("key", sa.String(length=100), nullable=False),
            sa.Column("value", sa.Text(), nullable=True),
            sa.Column("description", sa.String(length=500), nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=True,
            ),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("key", name="uq_system_secrets_key"),
        )

    _ensure_indexes(
        "system_secrets",
        [
            ("ix_system_secrets_key", ["key"], True),
            ("ix_system_secrets_updated_by", ["updated_by"], False),
        ],
    )


def downgrade() -> None:
    # Downgrade is best-effort.
    pass
