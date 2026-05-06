"""Add uid to users table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('uid', sa.String(36), nullable=False, server_default=sa.text("uuid_generate_v4()")))
    op.create_index('ix_users_uid', 'users', ['uid'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_uid', 'users')
    op.drop_column('users', 'uid')
