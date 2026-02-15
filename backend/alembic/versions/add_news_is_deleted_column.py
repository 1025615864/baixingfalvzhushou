"""add news is_deleted column

Revision ID: add_news_is_deleted
Revises: 1eb5bd51b80d
Create Date: 2026-01-30 22:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_news_is_deleted'
down_revision: Union[str, None] = '1eb5bd51b80d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if is_deleted column exists before adding (SQLite compatible)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('news')]
    
    if 'is_deleted' not in columns:
        # SQLite uses INTEGER for BOOLEAN (0=FALSE, 1=TRUE)
        op.add_column('news', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Drop is_deleted column (SQLite compatible)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('news')]
    
    if 'is_deleted' in columns:
        op.drop_column('news', 'is_deleted')
