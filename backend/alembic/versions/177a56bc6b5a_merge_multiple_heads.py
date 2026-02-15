"""merge_multiple_heads

Revision ID: 177a56bc6b5a
Revises: 83c191b154b7, q2r3s4t5u6v7
Create Date: 2026-02-03 21:51:42.729322

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '177a56bc6b5a'
down_revision: Union[str, None] = ('83c191b154b7', 'q2r3s4t5u6v7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
