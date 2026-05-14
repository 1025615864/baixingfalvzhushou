"""管理模型"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Index
from datetime import datetime

from app.database import Base


class CaseAuditLog(Base):
    """案例审核审计日志"""
    __tablename__ = "case_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, nullable=False, index=True)
    operator_id = Column(Integer, nullable=False)
    operator_name = Column(String(100), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    from_status = Column(String(20), nullable=True)
    to_status = Column(String(20), nullable=True)
    comment = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    __table_args__ = (
        Index("ix_audit_case_action", "case_id", "action"),
        Index("ix_audit_created_action", "created_at", "action"),
    )
