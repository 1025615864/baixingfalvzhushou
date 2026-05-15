"""裁判文书数据模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index, Float
from datetime import datetime

from app.database import Base


class CourtCase(Base):
    """裁判文书表"""
    __tablename__ = "court_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String(100), nullable=False, unique=True, index=True)
    case_type = Column(String(50), nullable=False, index=True)
    case_name = Column(String(500), nullable=False)
    case_date = Column(DateTime, nullable=True, index=True)
    court_name = Column(String(200), nullable=True, index=True)
    judge_name = Column(String(100), nullable=True)

    plaintiff = Column(Text, nullable=True)
    defendant = Column(Text, nullable=True)
    third_party = Column(Text, nullable=True)

    content = Column(Text, nullable=False)
    judgment_summary = Column(Text, nullable=True)
    judgment_result = Column(Text, nullable=True)

    legal_basis = Column(Text, nullable=True)
    applicable_laws = Column(String(500), nullable=True)
    applicable_articles = Column(String(500), nullable=True)

    case_amount = Column(Float, nullable=True, index=True)
    appeal_status = Column(String(20), nullable=True)
    execution_status = Column(String(20), nullable=True)

    keywords = Column(String(500), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(String(500), nullable=True)

    similarity_hash = Column(String(200), nullable=True, index=True)
    is_published = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)

    is_vectorized = Column(Boolean, default=False, index=True)
    vector_id = Column(String(200), nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)

    source = Column(String(200), nullable=True)
    source_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)

    case_metadata = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_case_court_date", "court_name", "case_date"),
        Index("ix_case_type_status", "case_type", "is_published"),
        Index("ix_case_amount_type", "case_amount", "case_type"),
    )


class LawArticle(Base):
    """法律条文表"""
    __tablename__ = "law_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    law_name = Column(String(200), nullable=False, index=True)
    law_number = Column(String(100), nullable=False, index=True)
    chapter = Column(String(200), nullable=True)
    section = Column(String(200), nullable=True)

    article_number = Column(String(20), nullable=False)
    article_title = Column(String(300), nullable=True)
    content = Column(Text, nullable=False)
    interpretation = Column(Text, nullable=True)

    effective_date = Column(DateTime, nullable=True, index=True)
    expiry_date = Column(DateTime, nullable=True)
    latest_version = Column(Boolean, default=True)

    jurisdiction = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    keywords = Column(String(500), nullable=True)

    related_articles = Column(String(500), nullable=True)
    related_cases = Column(String(500), nullable=True)
    amendment_history = Column(JSON, nullable=True)

    is_vectorized = Column(Boolean, default=False)
    vector_id = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_deleted = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_law_article_unique", "law_number", "article_number", unique=True),
        Index("ix_law_category_effective", "category", "effective_date"),
    )
