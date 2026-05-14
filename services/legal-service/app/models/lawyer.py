"""Lawyer and LawyerSchedule models"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, Float, Index, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Lawyer(Base):
    """律师表"""
    __tablename__ = "lawyers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    lawfirm_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=True)
    specialties: Mapped[list] = mapped_column(JSONB, default=list)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=5.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    consultation_count: Mapped[int] = mapped_column(Integer, default=0)
    response_time: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    city: Mapped[str] = mapped_column(String(50), nullable=True)
    avatar: Mapped[str] = mapped_column(String(500), nullable=True)
    price_range: Mapped[str] = mapped_column(String(50), nullable=True)
    firm_role: Mapped[str] = mapped_column(String(20), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    invited_by: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_lawyers_specialty_status", text("specialties"), postgresql_using="gin"),
        Index("idx_lawyers_city_rating", "city", "rating"),
    )

    def __repr__(self) -> str:
        return f"<Lawyer(id={self.id}, name={self.name}, status={self.status})>"


class LawyerSchedule(Base):
    """律师排班表"""
    __tablename__ = "lawyer_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    is_available: Mapped[bool] = mapped_column(Integer, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_schedule_lawyer_date", "lawyer_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<LawyerSchedule(id={self.id}, lawyer_id={self.lawyer_id}, date={self.date})>"