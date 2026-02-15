"""用户模型"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .user_security import UserSecuritySettings, UserDevice, LoginAudit


class User(Base):
    """用户表"""
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True)
    nickname: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(
        String(20), default="user")  # user/lawyer/admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    vip_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关联安全设置（一对一关系）
    security_settings: Mapped["UserSecuritySettings"] = relationship(
        "UserSecuritySettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    # 关联设备（一对多关系）
    devices: Mapped[list["UserDevice"]] = relationship(
        "UserDevice",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    # 关联登录审计记录（一对多关系）
    login_audits: Mapped[list["LoginAudit"]] = relationship(
        "LoginAudit",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
