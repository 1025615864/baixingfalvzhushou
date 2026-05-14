"""推荐数据模型"""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class UserFeature(Base):
    __tablename__ = "user_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class ItemFeature(Base):
    __tablename__ = "item_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("idx_item_feature_type_id", "item_type", "item_id", unique=True),)
