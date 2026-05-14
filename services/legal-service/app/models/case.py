"""案件模型"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LawCase(Base):
    __tablename__ = "law_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    consultation_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("consultations.id"), nullable=True, index=True)
    lawyer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("lawyers.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    client_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    progress_nodes: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    result_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), default="platform")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DispatchRecord(Base):
    __tablename__ = "dispatch_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(Integer, ForeignKey("consultations.id"), nullable=False, index=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("lawyers.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    dispatched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)