"""Add lawfirm management models

Revision ID: 003
Revises: 002
Create Date: 2024-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lawfirms', sa.Column('user_id', sa.Integer(), nullable=False, index=True))
    op.add_column('lawfirms', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('lawfirms', sa.Column('email', sa.String(100), nullable=True))
    op.add_column('lawfirms', sa.Column('description', sa.String(1000), nullable=True))
    op.add_column('lawfirms', sa.Column('license_image', sa.String(500), nullable=True))

    op.add_column('lawyers', sa.Column('firm_role', sa.String(20), nullable=True))
    op.add_column('lawyers', sa.Column('joined_at', sa.DateTime(), nullable=True))
    op.add_column('lawyers', sa.Column('invited_by', sa.Integer(), nullable=True))

    op.add_column('consultations', sa.Column('lawfirm_id', sa.Integer(), nullable=True, index=True))
    op.add_column('consultations', sa.Column('assigned_by_user_id', sa.Integer(), nullable=True))
    op.add_column('consultations', sa.Column('assigned_at', sa.DateTime(), nullable=True))

    op.create_index('idx_consult_lawfirm', 'consultations', ['lawfirm_id', 'status'])

    op.create_table(
        'lawfirm_invitations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('lawfirm_id', sa.Integer(), nullable=False, index=True),
        sa.Column('lawyer_id', sa.Integer(), nullable=False, index=True),
        sa.Column('invited_by_user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('firm_role', sa.String(20), default='associate'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_index('idx_invitation_lawfirm', 'lawfirm_invitations', ['lawfirm_id', 'status'])
    op.create_index('idx_invitation_lawyer', 'lawfirm_invitations', ['lawyer_id', 'status'])

    op.create_table(
        'lawfirm_verifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('lawfirm_id', sa.Integer(), nullable=False, unique=True, index=True),
        sa.Column('license_image', sa.String(500), nullable=True),
        sa.Column('id_card_image', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )

    op.create_table(
        'lawfirm_admins',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('lawfirm_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('role', sa.String(20), default='admin'),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_index('idx_firmadmin_firm_user', 'lawfirm_admins', ['lawfirm_id', 'user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_firmadmin_firm_user', table_name='lawfirm_admins')
    op.drop_table('lawfirm_admins')
    op.drop_table('lawfirm_verifications')
    op.drop_index('idx_invitation_lawyer', table_name='lawfirm_invitations')
    op.drop_index('idx_invitation_lawfirm', table_name='lawfirm_invitations')
    op.drop_table('lawfirm_invitations')
    op.drop_index('idx_consult_lawfirm', table_name='consultations')
    op.drop_column('consultations', 'assigned_at')
    op.drop_column('consultations', 'assigned_by_user_id')
    op.drop_column('consultations', 'lawfirm_id')
    op.drop_column('lawyers', 'invited_by')
    op.drop_column('lawyers', 'joined_at')
    op.drop_column('lawyers', 'firm_role')
    op.drop_column('lawfirms', 'license_image')
    op.drop_column('lawfirms', 'description')
    op.drop_column('lawfirms', 'email')
    op.drop_column('lawfirms', 'phone')
    op.drop_column('lawfirms', 'user_id')