"""咨询记录模型"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import ForeignKey, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class ConsultationStatus(str, enum.Enum):
    """咨询会话状态"""
    ACTIVE = "active"  # 进行中
    ARCHIVED = "archived"  # 已归档
    TRANSFERRED = "transferred"  # 已转人工
    CLOSED = "closed"  # 已关闭


class ConsultationCategory(str, enum.Enum):
    """咨询分类"""
    GENERAL = "general"  # 一般咨询
    LABOR = "labor"  # 劳动纠纷
    MARRIAGE = "marriage"  # 婚姻家庭
    CONTRACT = "contract"  # 合同纠纷
    PROPERTY = "property"  # 房产纠纷
    CRIMINAL = "criminal"  # 刑事案件
    TRAFFIC = "traffic"  # 交通事故
    INTELLECTUAL = "intellectual"  # 知识产权
    OTHER = "other"  # 其他


class Consultation(Base):
    """咨询会话表"""
    __tablename__: str = "consultations"

    __table_args__: tuple = (
        # 用户会话列表查询
        Index('ix_consultations_user_created', 'user_id', 'created_at'),
        # 状态查询
        Index('ix_consultations_status', 'status'),
        # 分类查询
        Index('ix_consultations_category', 'category'),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )

    # 分类和状态
    category: Mapped[str] = mapped_column(
        String(20), default=ConsultationCategory.GENERAL, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default=ConsultationStatus.ACTIVE, nullable=False
    )

    # 统计信息
    message_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # 转人工信息
    is_transferred: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    transferred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    transferred_to: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    transfer_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # 归档信息
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archive_reason: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # 关系
    user: Mapped[User | None] = relationship("User", foreign_keys=[user_id], backref="consultations")
    transferred_to_user: Mapped[User | None] = relationship("User", foreign_keys=[transferred_to])
    messages: Mapped[list[ChatMessage]] = relationship(
        "ChatMessage",
        back_populates="consultation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    """对话消息表"""
    __tablename__: str = "chat_messages"

    __table_args__: tuple = (
        # 会话消息查询
        Index('ix_chat_messages_consultation_created', 'consultation_id', 'created_at'),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    consultation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("consultations.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="user/assistant/system"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    # Token统计
    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="输入token数"
    )
    completion_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="输出token数"
    )
    total_tokens: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="总token数"
    )

    # 引用和参考
    references: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON格式存储引用的法条"
    )
    suggested_questions: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON格式存储建议的后续问题"
    )

    # 用户反馈
    rating: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="1=差评, 2=一般, 3=好评"
    )
    feedback: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="用户反馈"
    )
    is_helpful: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, comment="是否有帮助"
    )

    # 元数据
    model: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="使用的AI模型"
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="响应延迟(毫秒)"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 关系
    consultation: Mapped[Consultation] = relationship(
        "Consultation", back_populates="messages"
    )
