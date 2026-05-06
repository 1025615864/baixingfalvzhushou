"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('topics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=100), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('post_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_legal_category', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_topic_active_sort', 'topics', ['is_active', 'sort_order'], unique=False)

    op.create_table('posts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('author_name', sa.String(length=100), nullable=False),
        sa.Column('author_avatar', sa.String(length=500), nullable=True),
        sa.Column('is_lawyer', sa.Boolean(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('is_best_answer', sa.Boolean(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('like_count', sa.Integer(), nullable=True),
        sa.Column('comment_count', sa.Integer(), nullable=True),
        sa.Column('favorite_count', sa.Integer(), nullable=True),
        sa.Column('share_count', sa.Integer(), nullable=True),
        sa.Column('hot_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_posts_user_id', 'posts', ['user_id'], unique=False)
    op.create_index('ix_posts_category', 'posts', ['category'], unique=False)
    op.create_index('ix_posts_status', 'posts', ['status'], unique=False)
    op.create_index('ix_posts_created_at', 'posts', ['created_at'], unique=False)
    op.create_index('idx_posts_status_hot', 'posts', ['status', 'hot_score'], unique=False)
    op.create_index('idx_posts_status_created', 'posts', ['status', 'created_at'], unique=False)
    op.create_index('idx_posts_category_status', 'posts', ['category', 'status'], unique=False)

    op.create_table('post_likes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_post_likes_post_id', 'post_likes', ['post_id'], unique=False)
    op.create_index('ix_post_likes_user_id', 'post_likes', ['user_id'], unique=False)
    op.create_index('uq_post_like', 'post_likes', ['post_id', 'user_id'], unique=True)

    op.create_table('post_favorites',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_post_favorites_post_id', 'post_favorites', ['post_id'], unique=False)
    op.create_index('ix_post_favorites_user_id', 'post_favorites', ['user_id'], unique=False)
    op.create_index('uq_post_favorite', 'post_favorites', ['post_id', 'user_id'], unique=True)

    op.create_table('post_tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('tag_name', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_post_tags_post_id', 'post_tags', ['post_id'], unique=False)
    op.create_index('idx_post_tag', 'post_tags', ['post_id', 'tag_name'], unique=False)

    op.create_table('comments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('author_name', sa.String(length=100), nullable=False),
        sa.Column('author_avatar', sa.String(length=500), nullable=True),
        sa.Column('is_lawyer', sa.Boolean(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('reply_to_user_id', sa.Integer(), nullable=True),
        sa.Column('reply_to_user_name', sa.String(length=100), nullable=True),
        sa.Column('floor_number', sa.Integer(), nullable=True),
        sa.Column('like_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_comments_post_id', 'comments', ['post_id'], unique=False)
    op.create_index('ix_comments_user_id', 'comments', ['user_id'], unique=False)
    op.create_index('ix_comments_parent_id', 'comments', ['parent_id'], unique=False)
    op.create_index('ix_comments_status', 'comments', ['status'], unique=False)
    op.create_index('ix_comments_created_at', 'comments', ['created_at'], unique=False)
    op.create_index('idx_comment_post_parent', 'comments', ['post_id', 'parent_id'], unique=False)
    op.create_index('idx_comment_floor', 'comments', ['post_id', 'floor_number'], unique=False)

    op.create_table('reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reporter_id', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.String(length=20), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=50), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('handled_by', sa.Integer(), nullable=True),
        sa.Column('handled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('handle_result', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_reports_reporter_id', 'reports', ['reporter_id'], unique=False)
    op.create_index('ix_reports_target_id', 'reports', ['target_id'], unique=False)
    op.create_index('ix_reports_status', 'reports', ['status'], unique=False)
    op.create_index('ix_reports_created_at', 'reports', ['created_at'], unique=False)
    op.create_index('idx_report_target', 'reports', ['target_type', 'target_id'], unique=False)
    op.create_index('idx_report_status', 'reports', ['status', 'created_at'], unique=False)

    op.create_table('best_answers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('comment_id', sa.Integer(), nullable=False),
        sa.Column('selected_by', sa.Integer(), nullable=False),
        sa.Column('selected_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_best_answers_post_id', 'best_answers', ['post_id'], unique=False)
    op.create_index('uq_best_answer_post', 'best_answers', ['post_id'], unique=True)


def downgrade() -> None:
    op.drop_table('best_answers')
    op.drop_table('reports')
    op.drop_table('comments')
    op.drop_table('post_tags')
    op.drop_table('post_favorites')
    op.drop_table('post_likes')
    op.drop_table('posts')
    op.drop_table('topics')
