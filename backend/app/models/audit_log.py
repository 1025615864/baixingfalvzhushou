"""审计日志数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Index, JSON, Boolean
from sqlalchemy.sql import func
from .base import Base


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, nullable=True, index=True)
    user_name = Column(String(100), nullable=True)
    user_role = Column(String(50), nullable=True, index=True)

    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(200), nullable=True)

    method = Column(String(10), nullable=True)
    path = Column(String(500), nullable=False)
    query_params = Column(Text, nullable=True)
    request_body = Column(Text, nullable=True)

    ip_address = Column(String(50), nullable=True, index=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)

    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)

    duration_ms = Column(Integer, nullable=True)

    error_message = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False, index=True)

    extra_data = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_audit_user_action", "user_id", "action"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
        Index("ix_audit_created_at", "created_at"),
    )
