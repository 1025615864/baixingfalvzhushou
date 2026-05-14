"""Consultation and ChatMessage models"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Consultation(Base):
    """咨询表"""
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    lawfirm_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    ai_assisted: Mapped[bool] = mapped_column(Boolean, default=True)
    final_answer: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(50), nullable=True)
    assigned_by_user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_consult_user", "user_id", "created_at"),
        Index("idx_consult_lawyer", "lawyer_id", "status"),
        Index("idx_consult_category_status", "category", "status"),
        Index("idx_consult_lawfirm", "lawfirm_id", "status"),
        Index("idx_consult_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Consultation(id={self.id}, user_id={self.user_id}, status={self.status})>"


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role={self.role})>"