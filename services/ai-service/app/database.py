"""AI服务数据库引擎"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from .config.settings import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def import_audit_log_model():
    try:
        from services.common.models.audit_log import AuditLog
        return AuditLog
    except ImportError:
        from sqlalchemy import Column, String, Text, DateTime, Integer
        from sqlalchemy.sql import func

        class AuditLog(Base):
            __tablename__ = "audit_logs"

            id = Column(Integer, primary_key=True, autoincrement=True)
            user_id = Column(String(255), index=True)
            action = Column(String(100))
            resource_type = Column(String(100))
            resource_id = Column(String(255))
            details = Column(Text)
            ip_address = Column(String(45))
            created_at = Column(DateTime, server_default=func.now())

        return AuditLog
