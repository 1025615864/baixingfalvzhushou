"""管理相关数据模型"""
from sqlalchemy import Column, Integer, String, Text, Numeric, JSON, DateTime, Index
from datetime import datetime

from app.database import Base


class KnowledgeAuditLog(Base):
    """知识审核日志表"""
    __tablename__ = "knowledge_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_id = Column(Integer, nullable=False, index=True)
    operator_id = Column(Integer, nullable=True)
    operator_name = Column(String(100), nullable=True)
    action = Column(String(20), nullable=False)
    from_status = Column(String(20), nullable=True)
    to_status = Column(String(20), nullable=True)
    comment = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    __table_args__ = (
        Index("ix_audit_knowledge_action", "knowledge_id", "action"),
    )


class KnowledgeQualityScore(Base):
    """知识质量评分表"""
    __tablename__ = "knowledge_quality_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    knowledge_id = Column(Integer, nullable=False, index=True)
    accuracy = Column(Numeric(5, 2), nullable=True)
    completeness = Column(Numeric(5, 2), nullable=True)
    readability = Column(Numeric(5, 2), nullable=True)
    overall_score = Column(Numeric(5, 2), nullable=True)
    scorer_type = Column(String(20), nullable=False, default="manual")
    scorer_id = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    __table_args__ = (
        Index("ix_quality_knowledge_scorer", "knowledge_id", "scorer_type"),
    )
