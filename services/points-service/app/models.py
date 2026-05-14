"""积分数据模型"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class PointsUser(Base):
    __tablename__ = "points_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    balance: Mapped[int] = mapped_column(default=0)
    total_earned: Mapped[int] = mapped_column(default=0)
    total_spent: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PointsHistory(Base):
    __tablename__ = "points_history"
    __table_args__ = (
        Index("idx_points_history_user_created", "user_id", "created_at"),
        Index("idx_points_history_source", "source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    change: Mapped[int] = mapped_column()
    balance_after: Mapped[int] = mapped_column()
    source: Mapped[str] = mapped_column(String(50))
    reference_id: Mapped[str] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)


class PointsMallItem(Base):
    __tablename__ = "points_mall_items"
    __table_args__ = (
        Index("idx_points_mall_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    points_cost: Mapped[int] = mapped_column(Integer)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PointsExchangeOrder(Base):
    __tablename__ = "points_exchange_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    item_id: Mapped[int] = mapped_column(Integer)
    points_cost: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime] = mapped_column(nullable=True)


class DailyCheckIn(Base):
    __tablename__ = "daily_check_in"
    __table_args__ = (
        Index("ix_daily_check_in_user_date", "user_id", "check_in_date", unique=True),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    check_in_date: Mapped[str] = mapped_column(String(10))
    points_awarded: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
