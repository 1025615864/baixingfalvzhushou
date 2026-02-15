"""FAQ知识库模型"""
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, DateTime, Boolean, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class FAQ(Base):
    """FAQ知识库表"""

    __tablename__: str = "faqs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(
        String(500), nullable=False, index=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True)
    tags: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # JSON格式存储标签
    priority: Mapped[int] = mapped_column(
        Integer, default=0, index=True)  # 优先级，数字越大越靠前
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__: tuple[Index, ...] = (
        Index('idx_faqs_category_active', 'category', 'is_active'),
        Index('idx_faqs_priority_active', 'priority', 'is_active'),
        Index('idx_faqs_created_at', 'created_at'),
    )
