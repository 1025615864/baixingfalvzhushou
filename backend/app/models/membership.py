"""会员模型

存储用户的会员订阅信息。
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .user import User


class Membership(Base):
    """会员订阅表"""
    __tablename__: str = "memberships"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    level: Mapped[str] = mapped_column(
        String(20), default="free")  # free, monthly, annual, lifetime
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)  # 终身会员为null
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关联用户
    user: Mapped["User"] = relationship("User", back_populates="membership")