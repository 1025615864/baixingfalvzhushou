"""merge heads

Revision ID: 83c191b154b7
Revises: add_news_is_deleted, xxxx_add_refresh_tokens
Create Date: 2026-01-31 18:13:12.056275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83c191b154b7'
down_revision: Union[str, None] = ('add_news_is_deleted', 'xxxx_add_refresh_tokens')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
