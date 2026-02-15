"""merge heads final

Revision ID: n3o4p5q6r7s8
Revises: m2n3o4p5q6r7, l2m3n4o5p6q7
Create Date: 2026-01-21 06:20:00.000000

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "n3o4p5q6r7s8"
down_revision: Union[str, tuple[str, str], None] = ("m2n3o4p5q6r7", "l2m3n4o5p6q7")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
