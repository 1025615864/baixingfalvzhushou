"""LawyerConsultation (Appointment) model"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LawyerConsultation(Base):
    """律师咨询预约表"""
    __tablename__ = "lawyer_consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_appointment_lawyer_time", "lawyer_id", "scheduled_at"),
    )

    def __repr__(self) -> str:
        return f"<LawyerConsultation(id={self.id}, type={self.type}, status={self.status})>"