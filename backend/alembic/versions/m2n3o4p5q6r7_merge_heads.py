"""merge heads

Revision ID: m2n3o4p5q6r7
Revises: f1b2c3d4e5f6, k1l2m3n4o5p6
Create Date: 2026-01-21 06:10:00.000000

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "m2n3o4p5q6r7"
down_revision: Union[str, tuple[str, str], None] = ("f1b2c3d4e5f6", "k1l2m3n4o5p6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
