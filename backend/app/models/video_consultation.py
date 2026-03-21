"""视频咨询模型

存储视频咨询预约信息。
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text, DateTime, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .lawfirm import Lawyer


class VideoConsultation(Base):
    """视频咨询预约表"""
    __tablename__: str = "video_consultations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True)
    lawyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lawyers.id"), nullable=False, index=True)
    
    # 预约信息
    subject: Mapped[str] = mapped_column(String(200), nullable=False)  # 咨询主题
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # 问题描述
    category: Mapped[str | None] = mapped_column(
        String(50), nullable=True)  # 案件类型
    
    # 预约时间
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)  # 预约时间
    duration_minutes: Mapped[int] = mapped_column(
        Integer, default=30)  # 持续时间（分钟）
    
    # 视频会议信息
    meeting_room_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True)  # 会议房间ID
    meeting_password: Mapped[str | None] = mapped_column(
        String(50), nullable=True)  # 会议密码
    meeting_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # 会议链接
    
    # 状态
    status: Mapped[str] = mapped_column(
        String(20), default="pending")  # pending/confirmed/in_progress/completed/cancelled
    payment_status: Mapped[str] = mapped_column(
        String(20), default="pending")  # pending/paid/refunded
    payment_amount: Mapped[float] = mapped_column(Float, default=0.0)  # 支付金额
    
    # 会员权益
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否免费（会员权益）
    discount_rate: Mapped[float] = mapped_column(Float, default=1.0)  # 折扣率
    
    # 时间戳
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)  # 实际开始时间
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)  # 实际结束时间
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    user: Mapped["User"] = relationship("User", backref="video_consultations")
    lawyer: Mapped["Lawyer"] = relationship("Lawyer", backref="video_consultations")


class VideoConsultationUsage(Base):
    """用户视频咨询使用记录表（用于追踪会员免费次数）"""
    __tablename__: str = "video_consultation_usage"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True)
    year_month: Mapped[str] = mapped_column(
        String(7), nullable=False)  # 年月格式：YYYY-MM
    
    # 使用统计
    free_used: Mapped[int] = mapped_column(Integer, default=0)  # 已使用的免费次数
    paid_count: Mapped[int] = mapped_column(Integer, default=0)  # 付费次数
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    user: Mapped["User"] = relationship("User", backref="video_consultation_usage")


class VideoSchedule(Base):
    """律师视频咨询排班表"""
    __tablename__: str = "video_schedules"
    __table_args__: tuple[UniqueConstraint, ...] = (
        UniqueConstraint(
            "lawyer_id",
            "date",
            "start_time",
            name="uq_video_schedule_time"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lawyers.id"), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True)  # 日期
    start_time: Mapped[str] = mapped_column(
        String(10), nullable=False)  # 开始时间 HH:MM
    end_time: Mapped[str] = mapped_column(
        String(10), nullable=False)  # 结束时间 HH:MM
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否可用
    max_bookings: Mapped[int] = mapped_column(Integer, default=3)  # 最大预约数
    current_bookings: Mapped[int] = mapped_column(Integer, default=0)  # 当前预约数
    
    # 视频咨询设置
    video_consultation_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True)  # 是否开启视频咨询
    consultation_fee: Mapped[float] = mapped_column(
        Float, default=0.0)  # 视频咨询费用
    
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 备注
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    lawyer: Mapped["Lawyer"] = relationship("Lawyer", backref="video_schedules")