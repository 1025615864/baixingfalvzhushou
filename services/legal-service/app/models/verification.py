from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LawyerVerification(Base):
    __tablename__ = "lawyer_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    real_name: Mapped[str] = mapped_column(String(50), nullable=False)
    id_card_no: Mapped[str] = mapped_column(String(20), nullable=False)
    license_no: Mapped[str] = mapped_column(String(100), nullable=False)
    firm_name: Mapped[str] = mapped_column(String(200), nullable=False)
    id_card_front: Mapped[str | None] = mapped_column(String(500), nullable=True)
    id_card_back: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license_photo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    specialties: Mapped[str | None] = mapped_column(String(500), nullable=True)
    introduction: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))