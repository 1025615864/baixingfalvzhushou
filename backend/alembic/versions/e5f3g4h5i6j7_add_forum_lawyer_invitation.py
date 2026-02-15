from __future__ import annotations

from typing import Iterable

from alembic import op
import sqlalchemy as sa


revision: str = "e5f3g4h5i6j7"
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

    if "forum_lawyer_invitations" not in tables:
        op.create_table(
            "forum_lawyer_invitations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("post_id", sa.Integer(), nullable=False),
            sa.Column("lawyer_id", sa.Integer(), nullable=False),
            sa.Column("invited_by", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["post_id"], ["posts.id"]),
            sa.ForeignKeyConstraint(["lawyer_id"], ["lawyers.id"]),
            sa.ForeignKeyConstraint(["invited_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("post_id", "lawyer_id", name="uq_forum_lawyer_invitation_post_lawyer"),
        )

    _ensure_indexes(
        "forum_lawyer_invitations",
        [
            ("ix_forum_lawyer_invitations_post_id", ["post_id"], False),
            ("ix_forum_lawyer_invitations_lawyer_id", ["lawyer_id"], False),
            ("ix_forum_lawyer_invitations_invited_by", ["invited_by"], False),
            ("ix_forum_lawyer_invitations_status", ["status"], False),
            ("ix_forum_lawyer_invitations_expires_at", ["expires_at"], False),
        ],
    )


def downgrade() -> None:
    # Downgrade is best-effort.
    pass
