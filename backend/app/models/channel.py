"""渠道模型"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from ..database import Base


class Channel(Base):
    """渠道表 - 用于管理和追踪营销渠道"""
    __tablename__: str = "channels"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="渠道名称"
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="渠道代码，唯一标识"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="渠道描述"
    )
    url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="渠道链接"
    )
    type: Mapped[str] = mapped_column(
        String(20), default="other", comment="渠道类型: weixin/douyin/xiaohongshu/zhihu/bilibili/website/other"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", index=True, comment="状态: active/inactive"
    )
    visit_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="访问数"
    )
    register_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="注册数"
    )
    activation_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="激活数"
    )
    payment_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="支付/转化数"
    )
    total_revenue: Mapped[int] = mapped_column(
        Integer, default=0, comment="总收入(分)"
    )
    landing_config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="落地页配置(JSON格式)"
    )
    offer_config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="优惠配置(JSON格式)"
    )
    tracking_config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="追踪配置(JSON格式)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )

    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, code={self.code}, name={self.name}, status={self.status})>"

    @property
    def conversion_rate(self) -> float:
        """计算转化率"""
        if self.visit_count == 0:
            return 0.0
        return round(self.payment_count / self.visit_count * 100, 2)

    @property
    def activation_rate(self) -> float:
        """计算激活率"""
        if self.register_count == 0:
            return 0.0
        return round(self.activation_count / self.register_count * 100, 2)

    @property
    def payment_rate(self) -> float:
        """计算支付率"""
        if self.activation_count == 0:
            return 0.0
        return round(self.payment_count / self.activation_count * 100, 2)

    @property
    def avg_order_value(self) -> float:
        """计算平均订单价值"""
        if self.payment_count == 0:
            return 0.0
        return round(self.total_revenue / self.payment_count / 100, 2)