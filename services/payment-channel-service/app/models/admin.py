"""支付通道服务 - 管理模型

提供渠道配置、支付统计、审计日志等管理相关模型。
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Numeric, Boolean, JSON, Index

from ..database import Base


class ChannelConfig(Base):
    """渠道配置表"""

    __tablename__ = "channel_configs"
    __table_args__ = (
        Index("idx_channel_config_code", "channel_code", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_code = Column(String(50), unique=True, nullable=False, comment="渠道编码")
    channel_name = Column(String(100), nullable=False, comment="渠道名称")
    enabled = Column(Boolean, default=True, nullable=False, comment="是否启用")
    config_json = Column(JSON, nullable=True, comment="渠道配置JSON")
    fee_rate = Column(Numeric(8, 4), default=0, nullable=False, comment="费率")
    daily_limit = Column(Numeric(12, 2), nullable=True, comment="日限额")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")

    def __repr__(self):
        return f"<ChannelConfig(code={self.channel_code}, name={self.channel_name}, enabled={self.enabled})>"


class PaymentStats(Base):
    """支付统计表"""

    __tablename__ = "payment_stats"
    __table_args__ = (
        Index("idx_payment_stats_date", "stat_date"),
        Index("idx_payment_stats_channel", "channel_code"),
        Index("idx_payment_stats_date_channel", "stat_date", "channel_code"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(String(10), nullable=False, index=True, comment="统计日期 YYYY-MM-DD")
    channel_code = Column(String(50), nullable=False, index=True, comment="渠道编码")
    transaction_count = Column(Integer, default=0, nullable=False, comment="交易笔数")
    total_amount = Column(Numeric(12, 2), default=0, nullable=False, comment="总金额")
    success_count = Column(Integer, default=0, nullable=False, comment="成功笔数")
    success_rate = Column(Numeric(5, 2), default=0, nullable=False, comment="成功率(%)")
    fee_amount = Column(Numeric(12, 2), default=0, nullable=False, comment="手续费金额")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")

    def __repr__(self):
        return f"<PaymentStats(date={self.stat_date}, channel={self.channel_code}, count={self.transaction_count})>"


class PaymentAuditLog(Base):
    """支付审计日志表"""

    __tablename__ = "payment_audit_logs"
    __table_args__ = (
        Index("idx_audit_log_created", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, nullable=True, comment="操作目标ID")
    operator_id = Column(Integer, nullable=False, comment="操作人ID")
    operator_name = Column(String(64), nullable=False, comment="操作人姓名")
    action = Column(String(32), nullable=False, comment="操作动作")
    comment = Column(String(500), nullable=True, comment="备注")
    extra_data = Column(JSON, nullable=True, comment="扩展数据")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")

    def __repr__(self):
        return f"<PaymentAuditLog(id={self.id}, action={self.action}, operator={self.operator_name})>"
