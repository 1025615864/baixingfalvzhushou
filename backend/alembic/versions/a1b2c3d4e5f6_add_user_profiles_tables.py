"""add_user_profiles_tables

Revision ID: a1b2c3d4e5f6
Revises: n3o4p5q6r7s8
Create Date: 2026-01-21 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'n3o4p5q6r7s8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('interest_tags', sa.JSON(), nullable=True),
        sa.Column('interest_weights', sa.JSON(), nullable=True),
        sa.Column('preferred_content_types', sa.JSON(), nullable=True),
        sa.Column('usage_frequency', sa.String(length=20), nullable=True),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=True),
        sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('budget_range', sa.String(length=20), nullable=True),
        sa.Column('experience_level', sa.String(length=20), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_profiles_user_id'), 'user_profiles', ['user_id'], unique=True)

    op.create_table(
        'user_interest_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('behavior_type', sa.String(length=50), nullable=False),
        sa.Column('content_tags', sa.JSON(), nullable=True),
        sa.Column('interaction_type', sa.String(length=50), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('content_id', sa.String(length=100), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_interest_history_user_id'), 'user_interest_history', ['user_id'], unique=False)

    op.create_table(
        'user_tag_interactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tag', sa.String(length=100), nullable=False),
        sa.Column('interaction_count', sa.Integer(), nullable=True),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_weight', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_tag_interactions_user_id'), 'user_tag_interactions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_tag_interactions_tag'), 'user_tag_interactions', ['tag'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_tag_interactions_tag'), table_name='user_tag_interactions')
    op.drop_index(op.f('ix_user_tag_interactions_user_id'), table_name='user_tag_interactions')
    op.drop_table('user_tag_interactions')

    op.drop_index(op.f('ix_user_interest_history_user_id'), table_name='user_interest_history')
    op.drop_table('user_interest_history')

    op.drop_index(op.f('ix_user_profiles_user_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
