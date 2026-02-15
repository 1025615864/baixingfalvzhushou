"""merge heads for news is_deleted fix

Revision ID: 1eb5bd51b80d
Revises: 68cccd7313a6, add_contract_review_history
Create Date: 2026-01-30 14:47:35.885176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1eb5bd51b80d'
down_revision: Union[str, None] = ('68cccd7313a6', 'add_contract_review_history')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
