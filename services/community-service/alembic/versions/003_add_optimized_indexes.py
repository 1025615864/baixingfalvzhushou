"""add optimized indexes

Revision ID: 003
Revises: 002
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'idx_posts_user_status',
        'posts',
        ['user_id', 'status'],
        unique=False
    )

    op.create_index(
        'idx_posts_category_status_created',
        'posts',
        ['category', 'status', 'created_at'],
        unique=False
    )

    op.create_index(
        'idx_comments_user_status',
        'comments',
        ['user_id', 'status'],
        unique=False
    )

    op.create_index(
        'idx_posts_is_pinned_hot',
        'posts',
        ['is_pinned', 'hot_score'],
        unique=False
    )

    op.create_index(
        'idx_posts_is_featured',
        'posts',
        ['is_featured'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_posts_user_status', table_name='posts')
    op.drop_index('idx_posts_category_status_created', table_name='posts')
    op.drop_index('idx_comments_user_status', table_name='comments')
    op.drop_index('idx_posts_is_pinned_hot', table_name='posts')
    op.drop_index('idx_posts_is_featured', table_name='posts')
