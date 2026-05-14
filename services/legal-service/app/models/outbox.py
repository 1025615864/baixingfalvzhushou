"""Kafka Outbox 事件表模型"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, JSON, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class OutboxEvent(Base):
    """Outbox 事件表 - 确保 Kafka 事件不丢失"""
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True,
        comment="pending|published|failed"
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(String(1000), nullable=True)

    __table_args__ = (
        Index("idx_outbox_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<OutboxEvent(id={self.id}, type={self.event_type}, status={self.status})>"
