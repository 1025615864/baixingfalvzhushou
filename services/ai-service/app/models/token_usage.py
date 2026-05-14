"""Token消耗记录数据模型"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TokenUsageRecord(Base):
    """Token消耗记录表"""
    __tablename__ = "token_usage_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(100), index=True)
    model_name: Mapped[str] = mapped_column(String(100))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=True)
    cost_cny: Mapped[float] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_token_usage_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<TokenUsageRecord(id={self.id}, conversation_id={self.conversation_id}, total_tokens={self.total_tokens})>"