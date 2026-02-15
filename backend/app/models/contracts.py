from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ..database import Base


class ContractReviewHistory(Base):
    """合同审查历史记录"""
    __tablename__ = "contract_review_history"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: __import__('uuid').uuid4().hex
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    
    # 文件信息
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_type: Mapped[str | None] = mapped_column(String(100))
    content_type: Mapped[str | None] = mapped_column(String(100))
    
    # 文本提取信息
    text_chars: Mapped[int] = mapped_column(Integer, default=0)
    text_preview: Mapped[str] = mapped_column(Text)
    
    # 审查结果
    risk_level: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", name="contract_risk_level"),
        default="low",
        index=True
    )
    risk_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 报告数据
    report_json: Mapped[dict | None] = mapped_column(JSON)
    report_markdown: Mapped[str] = mapped_column(Text)
    
    # 请求信息
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    focus: Mapped[str | None] = mapped_column(Text)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )