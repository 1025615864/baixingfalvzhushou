"""initial tables

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'consultations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('lawyer_id', sa.Integer(), nullable=True, index=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('ai_assisted', sa.Boolean(), default=True),
        sa.Column('final_answer', sa.Text(), nullable=True),
        sa.Column('city', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), index=True),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_consult_user', 'consultations', ['user_id', 'created_at'])
    op.create_index('idx_consult_lawyer', 'consultations', ['lawyer_id', 'status'])
    op.create_index('idx_consult_category_status', 'consultations', ['category', 'status'])

    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('consultation_id', sa.Integer(), nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), index=True),
    )

    op.create_table(
        'lawyers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, unique=True, index=True),
        sa.Column('lawfirm_id', sa.Integer(), nullable=True, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('title', sa.String(100), nullable=True),
        sa.Column('specialties', postgresql.JSON(), default=list),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('rating', sa.Float(), default=5.0),
        sa.Column('rating_count', sa.Integer(), default=0),
        sa.Column('consultation_count', sa.Integer(), default=0),
        sa.Column('response_time', sa.Integer(), default=0),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('city', sa.String(50), nullable=True),
        sa.Column('avatar', sa.String(500), nullable=True),
        sa.Column('price_range', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_lawyers_city_rating', 'lawyers', ['city', 'rating'])

    op.create_table(
        'lawfirms',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('license_no', sa.String(50), nullable=True, unique=True),
        sa.Column('province', sa.String(50), nullable=True),
        sa.Column('city', sa.String(50), nullable=True),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('lawyer_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )

    op.create_table(
        'lawyer_consultations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('consultation_id', sa.Integer(), nullable=False, index=True),
        sa.Column('lawyer_id', sa.Integer(), nullable=False, index=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('price', sa.Float(), default=0.0),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_appointment_lawyer_time', 'lawyer_consultations', ['lawyer_id', 'scheduled_at'])

    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('consultation_id', sa.Integer(), nullable=False, unique=True, index=True),
        sa.Column('lawyer_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), index=True),
    )
    op.create_index('idx_reviews_lawyer_created', 'reviews', ['lawyer_id', 'created_at'])

    op.create_table(
        'lawyer_schedules',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('lawyer_id', sa.Integer(), nullable=False, index=True),
        sa.Column('date', sa.DateTime(), nullable=False, index=True),
        sa.Column('start_time', sa.String(10), nullable=False),
        sa.Column('end_time', sa.String(10), nullable=False),
        sa.Column('is_available', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_schedule_lawyer_date', 'lawyer_schedules', ['lawyer_id', 'date'])

    op.create_table(
        'legal_documents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('consultation_id', sa.Integer(), nullable=False, index=True),
        sa.Column('lawyer_id', sa.Integer(), nullable=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('generated_by_ai', sa.Boolean(), default=False),
        sa.Column('ai_prompt', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), index=True),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('idx_document_consultation', 'legal_documents', ['consultation_id', 'created_at'])
    op.create_index('idx_document_lawyer', 'legal_documents', ['lawyer_id', 'status'])
    op.create_index('idx_document_type_status', 'legal_documents', ['document_type', 'status'])

    op.create_table(
        'document_templates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False, index=True),
        sa.Column('template_content', sa.Text(), nullable=False),
        sa.Column('required_fields', postgresql.JSON(), default=list),
        sa.Column('optional_fields', postgresql.JSON(), default=list),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table('document_templates')
    op.drop_table('legal_documents')
    op.drop_table('lawyer_schedules')
    op.drop_table('reviews')
    op.drop_table('lawyer_consultations')
    op.drop_table('lawfirms')
    op.drop_table('lawyers')
    op.drop_table('chat_messages')
    op.drop_table('consultations')