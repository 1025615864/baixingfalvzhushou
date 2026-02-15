"""用户安全中心模型"""
from __future__ import annotations

from datetime import datetime
from typing import List, TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import Integer, String, DateTime, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .user import User


class DeviceType(str, PyEnum):
    """设备类型枚举"""
    WEB = "web"
    MOBILE = "mobile"
    APP = "app"


class LoginAction(str, PyEnum):
    """登录操作类型枚举"""
    LOGIN = "login"
    LOGOUT = "logout"
    TWO_FA_VERIFY = "2fa_verify"
    FAILED = "failed"
    PASSWORD_CHANGE = "password_change"


class UserSecuritySettings(Base):
    """用户安全设置表"""
    __tablename__: str = "user_security_settings"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # TOTP双因素认证密钥（加密存储）
    totp_secret: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    # 是否启用2FA
    is_2fa_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # 备用恢复码列表
    backup_codes: Mapped[List[str] | None] = mapped_column(
        JSON, nullable=True
    )
    # 密码最后修改时间
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 登录提醒开关
    login_alert_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    # 异常活动提醒开关
    unusual_activity_alert: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 关联用户
    user: Mapped["User"] = relationship("User", back_populates="security_settings")


class UserDevice(Base):
    """用户登录设备表"""
    __tablename__: str = "user_devices"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # 设备唯一标识
    device_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    # 设备名称
    device_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    # 设备类型
    device_type: Mapped[DeviceType] = mapped_column(
        Enum(DeviceType, name="device_type_enum", native_enum=True), nullable=False
    )
    # 用户代理字符串
    user_agent: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    # IP地址
    ip_address: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    # 地理位置
    location: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    # 首次登录时间
    first_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 最后登录时间
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # 是否为当前设备
    is_current: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # 是否已撤销
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # 撤销时间
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Token指纹（用于验证）
    token_fingerprint: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )

    # 关联用户
    user: Mapped["User"] = relationship("User", back_populates="devices")


class LoginAudit(Base):
    """用户登录审计日志表"""
    __tablename__: str = "user_login_audits"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # 操作类型
    action: Mapped[LoginAction] = mapped_column(
        Enum(LoginAction, name="login_action_enum", native_enum=True), nullable=False
    )
    # IP地址
    ip_address: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    # 用户代理字符串
    user_agent: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    # 设备标识（可空，关联设备表）
    device_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    # 操作是否成功
    success: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
    # 失败原因
    failure_reason: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    # 地理位置
    location: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # 关联用户
    user: Mapped["User"] = relationship("User", back_populates="login_audits")
    # 注意：device_id 是字符串标识，不是外键关联
    # 如需关联设备，需要通过 device_id 手动查询