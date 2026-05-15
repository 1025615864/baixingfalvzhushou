"""档案库数据模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index, ForeignKey
from datetime import datetime

from app.database import Base


class LegalCase(Base):
    """案例表"""
    __tablename__ = "legal_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String(100), nullable=True, unique=True)
    case_type = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    facts = Column(Text, nullable=False)
    legal_basis = Column(Text, nullable=True)
    judgment = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    category = Column(String(200), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("case_categories.id"), nullable=True, index=True)
    keywords = Column(String(500), nullable=True)

    # 法院信息
    court = Column(String(200), nullable=True, index=True)
    court_level = Column(String(50), nullable=True)  # 基层、中院、高院、最高院
    judge_date = Column(DateTime, nullable=True, index=True)

    # 案件类型细分
    cause_of_action = Column(String(100), nullable=True, index=True)  # 案由
    judgment_result = Column(String(100), nullable=True)  # 判决结果
    key_points = Column(Text, nullable=True)  # 关键要点
    applicable_laws = Column(Text, nullable=True)  # 适用法律

    # 来源信息
    source = Column(String(200), nullable=True)
    source_url = Column(String(500), nullable=True)
    is_guiding_case = Column(Boolean, default=False, index=True)  # 是否为指导性案例

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

    # 统计
    view_count = Column(Integer, default=0)
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
        Index("ix_cases_status_vectorized", "status", "is_vectorized"),
        Index("ix_cases_court_level", "court_level", "status"),
        Index("ix_cases_cause_status", "cause_of_action", "status"),
    )


class CaseCategory(Base):
    """案例分类表"""
    __tablename__ = "case_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    parent_id = Column(Integer, nullable=True, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)