from __future__ import annotations

from typing import Iterable

from alembic import op
import sqlalchemy as sa


revision: str = "g8h9i0j1k2l3"
down_revision: str | None = "f6g4h5i6j7k8"
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

    if "ai_model_configs" not in tables:
        op.create_table(
            "ai_model_configs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("model_id", sa.String(length=200), nullable=False),
            sa.Column("api_key", sa.Text(), nullable=True),
            sa.Column("base_url", sa.String(length=500), nullable=True),
            sa.Column("enabled", sa.Boolean(), server_default="1", nullable=False),
            sa.Column("weight", sa.Integer(), server_default="1", nullable=False),
            sa.Column("max_tokens", sa.Integer(), nullable=True),
            sa.Column("temperature", sa.Float(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=True,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=True,
            ),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("updated_by", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("model_id", name="uq_ai_model_configs_model_id"),
        )

        _ensure_indexes(
            "ai_model_configs",
            [
                ("ix_ai_model_configs_name", ["name"], False),
                ("ix_ai_model_configs_model_id", ["model_id"], True),
                ("ix_ai_model_configs_enabled", ["enabled"], False),
                ("ix_ai_model_configs_created_by", ["created_by"], False),
                ("ix_ai_model_configs_updated_by", ["updated_by"], False),
            ],
        )


def downgrade() -> None:
    # Downgrade is best-effort.
    pass
