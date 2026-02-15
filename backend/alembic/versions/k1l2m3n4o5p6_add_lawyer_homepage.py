"""add lawyer homepage

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-01-21 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'k1l2m3n4o5p6'
down_revision: Union[str, None] = 'j0k1l2m3n4o5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建律师主页定制表
    op.create_table(
        'lawyer_homepages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('banner_image', sa.String(length=255), nullable=True),
        sa.Column('profile_image', sa.String(length=255), nullable=True),
        sa.Column('slogan', sa.String(length=200), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('specialties_display', sa.Text(), nullable=True),
        sa.Column('achievements', sa.Text(), nullable=True),
        sa.Column('education', sa.Text(), nullable=True),
        sa.Column('service_areas', sa.Text(), nullable=True),
        sa.Column('service_hours', sa.String(length=200), nullable=True),
        sa.Column('response_time', sa.String(length=100), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('contact_email', sa.String(length=100), nullable=True),
        sa.Column('wechat_qrcode', sa.String(length=255), nullable=True),
        sa.Column('weibo_url', sa.String(length=255), nullable=True),
        sa.Column('linkedin_url', sa.String(length=255), nullable=True),
        sa.Column('zhihu_url', sa.String(length=255), nullable=True),
        sa.Column('case_studies', sa.Text(), nullable=True),
        sa.Column('video_url', sa.String(length=255), nullable=True),
        sa.Column('video_cover', sa.String(length=255), nullable=True),
        sa.Column('seo_title', sa.String(length=100), nullable=True),
        sa.Column('seo_description', sa.String(length=500), nullable=True),
        sa.Column('seo_keywords', sa.String(length=500), nullable=True),
        sa.Column('theme_color', sa.String(length=20), nullable=True),
        sa.Column('background_color', sa.String(length=20), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['lawyer_id'], ['lawyers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lawyer_id')
    )
    op.create_index(op.f('ix_lawyer_homepages_lawyer_id'), 'lawyer_homepages', ['lawyer_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_lawyer_homepages_lawyer_id'), table_name='lawyer_homepages')
    op.drop_table('lawyer_homepages')
