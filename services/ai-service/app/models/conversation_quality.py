"""对话质量评估数据模型"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, JSON, Float, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ConversationQualityRecord(Base):
    """对话质量记录表"""
    __tablename__ = "conversation_quality_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(100), index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    feedback: Mapped[int] = mapped_column(Integer, nullable=True)
    issues: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_conversation_quality_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ConversationQualityRecord(id={self.id}, conversation_id={self.conversation_id}, score={self.quality_score})>"