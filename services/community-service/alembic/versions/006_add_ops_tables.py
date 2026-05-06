"""add ops tables

Revision ID: 006
Revises: 005
Create Date: 2026-03-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ops_role',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ops_role_user_role', 'ops_role', ['user_id', 'role'], unique=True)
    op.create_index('idx_ops_role_user_id', 'ops_role', ['user_id'])

    op.create_table(
        'ops_audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('operator_role', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_operator_time', 'ops_audit_log', ['operator_id', 'created_at'])
    op.create_index('idx_audit_action_time', 'ops_audit_log', ['action', 'created_at'])
    op.create_index('idx_audit_target', 'ops_audit_log', ['target_type', 'target_id'])
    op.create_index('idx_audit_log_created_at', 'ops_audit_log', ['created_at'])

    op.create_table(
        'user_penalty',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('related_post_id', sa.Integer(), nullable=True),
        sa.Column('related_comment_id', sa.Integer(), nullable=True),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('duration_hours', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_by', sa.Integer(), nullable=True),
        sa.Column('revoked_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_penalty_user_active', 'user_penalty', ['user_id', 'is_active'])
    op.create_index('idx_penalty_expires', 'user_penalty', ['expires_at'])

    op.create_table(
        'user_appeal',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('penalty_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('handler_id', sa.Integer(), nullable=True),
        sa.Column('handle_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('handled_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_appeal_user_id', 'user_appeal', ['user_id'])
    op.create_index('idx_appeal_status', 'user_appeal', ['status'])

    op.create_table(
        'announcement',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=True, default='global'),
        sa.Column('scope_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=True, default=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_announcement_scope_active', 'announcement', ['scope', 'is_active'])

    op.create_table(
        'ops_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ops_config_key', 'ops_config', ['key'], unique=True)

    op.create_table(
        'recommendation_slot',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=50), nullable=True),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_recommendation_position', 'recommendation_slot', ['position'])
    op.create_index('idx_recommendation_active', 'recommendation_slot', ['is_active'])


def downgrade() -> None:
    op.drop_index('idx_recommendation_active', table_name='recommendation_slot')
    op.drop_index('idx_recommendation_position', table_name='recommendation_slot')
    op.drop_table('recommendation_slot')

    op.drop_index('idx_ops_config_key', table_name='ops_config')
    op.drop_table('ops_config')

    op.drop_index('idx_announcement_scope_active', table_name='announcement')
    op.drop_table('announcement')

    op.drop_index('idx_appeal_status', table_name='user_appeal')
    op.drop_index('idx_appeal_user_id', table_name='user_appeal')
    op.drop_table('user_appeal')

    op.drop_index('idx_penalty_expires', table_name='user_penalty')
    op.drop_index('idx_penalty_user_active', table_name='user_penalty')
    op.drop_table('user_penalty')

    op.drop_index('idx_audit_log_created_at', table_name='ops_audit_log')
    op.drop_index('idx_audit_target', table_name='ops_audit_log')
    op.drop_index('idx_audit_action_time', table_name='ops_audit_log')
    op.drop_index('idx_audit_operator_time', table_name='ops_audit_log')
    op.drop_table('ops_audit_log')

    op.drop_index('idx_ops_role_user_id', table_name='ops_role')
    op.drop_index('idx_ops_role_user_role', table_name='ops_role')
    op.drop_table('ops_role')
