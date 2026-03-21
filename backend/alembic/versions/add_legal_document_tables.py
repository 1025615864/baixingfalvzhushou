"""add_legal_document_tables

添加法律文书商城相关表

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'legal_doc_001'
down_revision = None  # 设置为当前最新的迁移版本
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 法律文书商品表
    op.create_table(
        'legal_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('points_required', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('member_prices_json', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_free', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rating', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tags', sa.String(500), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('custom_service_available', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('custom_service_price', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_legal_documents_category', 'legal_documents', ['category'])
    op.create_index('ix_legal_documents_category_active', 'legal_documents', ['category', 'is_active'])
    op.create_index('ix_legal_documents_featured', 'legal_documents', ['is_featured', 'is_active'])

    # 法律文书订单表
    op.create_table(
        'legal_document_orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_no', sa.String(64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('points_spent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('original_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('discount_amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('payment_method', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['document_id'], ['legal_documents.id'])
    )
    op.create_index('ix_legal_document_orders_order_no', 'legal_document_orders', ['order_no'], unique=True)
    op.create_index('ix_legal_document_orders_user', 'legal_document_orders', ['user_id', 'status'])
    op.create_index('ix_legal_document_orders_document', 'legal_document_orders', ['document_id'])
    op.create_index('ix_legal_document_orders_status', 'legal_document_orders', ['status'])

    # 法律文书收藏表
    op.create_table(
        'legal_document_favorites',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['document_id'], ['legal_documents.id']),
        sa.UniqueConstraint('user_id', 'document_id', name='uq_user_document_favorite')
    )
    op.create_index('ix_legal_document_favorites_user', 'legal_document_favorites', ['user_id'])
    op.create_index('ix_legal_document_favorites_document', 'legal_document_favorites', ['document_id'])


def downgrade() -> None:
    op.drop_table('legal_document_favorites')
    op.drop_table('legal_document_orders')
    op.drop_table('legal_documents')