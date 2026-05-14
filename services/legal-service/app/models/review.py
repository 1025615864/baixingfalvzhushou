"""Review model"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Review(Base):
    """用户评价表"""
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_reviews_lawyer_created", "lawyer_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, lawyer_id={self.lawyer_id}, rating={self.rating})>"