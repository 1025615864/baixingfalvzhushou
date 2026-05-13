"""知识库数据模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class LegalKnowledge(Base):
    """法律知识表"""
    __tablename__ = "legal_knowledge"

    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_type = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    article_number = Column(String(100), nullable=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    category = Column(String(200), nullable=True, index=True)
    keywords = Column(String(500), nullable=True)
    source = Column(String(200), nullable=True)

    # 向量化和索引状态
    is_vectorized = Column(Boolean, default=False, index=True)
    vector_id = Column(String(200), nullable=True)
    vector_indexed = Column(Boolean, default=False)
    vector_indexed_at = Column(DateTime, nullable=True)

    # 生命周期状态
    status = Column(String(20), default="draft", index=True)  # draft, pending_review, published, archived

    # 版本管理
    version = Column(Integer, default=1)
    effective_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)

    # 法律相关字段
    law_number = Column(String(100), nullable=True)
    jurisdiction = Column(String(100), nullable=True)

    # 权重
    weight = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)

    # 审计字段
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)

    meta_data = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_knowledge_status_vectorized", "status", "is_vectorized"),
        Index("ix_knowledge_category_status", "category", "status"),
    )


class KnowledgeCategory(Base):
    """知识分类表"""
    __tablename__ = "knowledge_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    parent_id = Column(Integer, nullable=True, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)