"""律所资质审核表"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LawFirmVerification(Base):
    """律所资质审核表"""
    __tablename__ = "lawfirm_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawfirm_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    license_image: Mapped[str] = mapped_column(String(500), nullable=True)
    id_card_image: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<LawFirmVerification(id={self.id}, lawfirm_id={self.lawfirm_id}, status={self.status})>"