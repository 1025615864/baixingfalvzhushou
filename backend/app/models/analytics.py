"""数据分析相关模型"""
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class UserBehaviorLog(Base):
    """用户行为日志表"""

    __tablename__: str = "user_behavior_logs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True)  # 用户ID，可为空（未登录用户）
    # 行为类型：page_view/click/submit/search/...
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # 资源类型：post/consultation/lawyer/...
    resource_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True)
    resource_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True)  # 资源ID
    metadata_json: Mapped[str | None] = mapped_column(
        "metadata", Text, nullable=True)  # 额外元数据，JSON格式
    ip_address: Mapped[str | None] = mapped_column(
        String(50), nullable=True)  # IP地址
    user_agent: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # 用户代理
    referrer: Mapped[str | None] = mapped_column(
        String(500), nullable=True)  # 来源页面
    session_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True)  # 会话ID
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__: tuple[Index, ...] = (
        Index('idx_user_behavior_logs_user_action', 'user_id', 'action'),
        Index(
            'idx_user_behavior_logs_resource',
            'resource_type',
            'resource_id'),
        Index('idx_user_behavior_logs_created_at', 'created_at'),
    )
