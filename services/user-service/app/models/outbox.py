"""Outbox 模型 - 确保事件可靠发布"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class OutboxEvent(Base):
    """Outbox 事件表 - 确保事件可靠发布

    工作机制：
    1. 业务操作和事件写入在同一事务
    2. 后台任务扫描 outbox 表发送到 Kafka
    3. 发送成功后标记为 published
    4. 失败重试最多 5 次
    """
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        index=True
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_outbox_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<OutboxEvent(id={self.id}, event_type={self.event_type}, status={self.status})>"


class OutboxStatus:
    """Outbox 状态常量"""
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
