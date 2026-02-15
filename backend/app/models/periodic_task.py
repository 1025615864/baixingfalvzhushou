"""周期任务运行记录模型"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import Integer, String, DateTime, Text, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .user import User


class TaskStatus(str, PyEnum):
    """任务执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PeriodicTaskRun(Base):
    """周期任务运行记录表"""
    __tablename__: str = "periodic_task_runs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    task_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True)
    task_key: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True)  # 任务唯一标识
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="task_status_enum", create_type=False),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(
        Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True)  # JSON格式结果摘要
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<PeriodicTaskRun(id={self.id}, task='{self.task_name}', status='{self.status}')>"
