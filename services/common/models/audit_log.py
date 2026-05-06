"""审计日志模型"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

Base = DeclarativeBase()


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    service = Column(String(50), index=True)
    user_id = Column(Integer, nullable=True)
    user_role = Column(String(50), nullable=True)
    action = Column(String(50), index=True)
    resource_type = Column(String(50), index=True)
    resource_id = Column(Integer)
    changes = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    __table_args__ = (
        Index("ix_audit_service_resource", "service", "resource_type", "resource_id"),
        Index("ix_audit_user_time", "user_id", "created_at"),
        Index("ix_audit_action_time", "action", "created_at"),
    )
