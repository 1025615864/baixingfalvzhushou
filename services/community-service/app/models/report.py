"""举报模型"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    reporter_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    handled_by: Mapped[int] = mapped_column(Integer, nullable=True)
    handled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    handle_result: Mapped[str] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)

    __table_args__ = (
        Index("idx_report_target", "target_type", "target_id"),
        Index("idx_report_status", "status", "created_at"),
    )
