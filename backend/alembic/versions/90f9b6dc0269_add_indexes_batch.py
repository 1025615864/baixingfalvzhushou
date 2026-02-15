"""add_indexes_batch

Revision ID: 90f9b6dc0269
Revises: o1p2q3r4s5t6
Create Date: 2026-01-24 19:55:30.427373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90f9b6dc0269'
down_revision: Union[str, None] = 'o1p2q3r4s5t6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_comments_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_comments_post_id'), ['post_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_comments_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_posts_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_posts_user_id'), ['user_id'], unique=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_nickname'), ['nickname'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_nickname'))

    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_posts_user_id'))
        batch_op.drop_index(batch_op.f('ix_posts_created_at'))

    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_comments_user_id'))
        batch_op.drop_index(batch_op.f('ix_comments_post_id'))
        batch_op.drop_index(batch_op.f('ix_comments_created_at'))
