"""内容审核相关模型"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base

if TYPE_CHECKING:
    pass


class ModerationRecord(Base):
    """内容审核记录表

    用于持久化存储内容审核的结果，支持查询和统计。
    """
    __tablename__: str = "moderation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="内容哈希值")
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="内容类型: post/comment/news/etc")
    risk_score: Mapped[int] = mapped_column(Integer, default=0, comment="风险分数 0-100")
    risk_level: Mapped[str] = mapped_column(String(20), default="low", comment="风险等级: low/medium/high")
    decision: Mapped[str] = mapped_column(String(20), default="pending", comment="审核决定: approved/rejected/pending_review")
    matched_keywords: Mapped[str | None] = mapped_column(Text, nullable=True, comment="匹配的关键词(JSON)")
    ai_review_result: Mapped[str | None] = mapped_column(Text, nullable=True, comment="AI审核结果(JSON)")
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="提交用户ID")
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, comment="IP地址")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )
    moderated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="审核时间")

    __table_args__ = (
        Index("idx_moderation_content_hash", "content_hash"),
        Index("idx_moderation_decision", "decision"),
        Index("idx_moderation_created_at", "created_at"),
    )
