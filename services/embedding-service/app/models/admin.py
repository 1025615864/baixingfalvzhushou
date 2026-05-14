from sqlalchemy import Column, Integer, String, Numeric, DateTime, Index
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

Base = DeclarativeBase()


class EmbeddingCallStats(Base):
    __tablename__ = "embedding_call_stats"

    id = Column(Integer, primary_key=True)
    stat_date = Column(String(10), index=True)
    model_name = Column(String(100), index=True)
    call_count = Column(Integer, nullable=False, default=0)
    avg_latency_ms = Column(Numeric(10, 2), nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("ix_ecs_date_model", "stat_date", "model_name"),
    )


class ServiceQuota(Base):
    __tablename__ = "service_quotas"

    id = Column(Integer, primary_key=True)
    service_name = Column(String(100), unique=True, index=True)
    daily_limit = Column(Integer, nullable=False, default=0)
    used_count = Column(Integer, nullable=False, default=0)
    reset_date = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
