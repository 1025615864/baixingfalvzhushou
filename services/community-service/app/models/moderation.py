"""审核队列表"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, Boolean, JSON, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ModerationQueue(Base):
    __tablename__ = "moderation_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content_preview: Mapped[str] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=5, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    report_reason: Mapped[str] = mapped_column(String(500), nullable=True)
    reporter_id: Mapped[int] = mapped_column(Integer, nullable=True)
    ai_confidence: Mapped[float] = mapped_column(Integer, nullable=True)
    ai_analysis: Mapped[str] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int] = mapped_column(Integer, nullable=True)
    review_decision: Mapped[str] = mapped_column(String(20), nullable=True)
    review_reason: Mapped[str] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_moderation_queue_priority_status", "priority", "status"),
        Index("idx_moderation_queue_content", "content_type", "content_id"),
    )

    def __repr__(self):
        return f"<ModerationQueue(id={self.id}, type={self.content_type}, status={self.status})>"


def utc_now():
    return datetime.now(timezone.utc)
