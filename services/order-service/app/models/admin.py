"""订单服务 - 管理模型

提供退款审计日志、订单统计等管理相关模型。
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, Numeric, Index, JSON

from app.database import Base


class RefundAudit(Base):
    """退款审计日志"""

    __tablename__ = "refund_audits"
    __table_args__ = (
        Index("idx_refund_audit_order", "order_id"),
        Index("idx_refund_audit_created", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False, index=True, comment="订单 ID")
    auditor_id = Column(Integer, nullable=False, comment="审核人 ID")
    auditor_name = Column(String(64), nullable=False, comment="审核人姓名")
    action = Column(String(16), nullable=False, comment="审核动作: approve/reject")
    comment = Column(Text, nullable=True, comment="审核备注")
    extra_data = Column(JSON, nullable=True, comment="扩展数据")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")

    def __repr__(self):
        return f"<RefundAudit(id={self.id}, order_id={self.order_id}, action='{self.action}')>"


class OrderStats(Base):
    """订单统计"""

    __tablename__ = "order_stats"
    __table_args__ = (
        Index("idx_order_stats_date", "stat_date", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(String(10), nullable=False, unique=True, comment="统计日期 YYYY-MM-DD")
    total_orders = Column(Integer, default=0, comment="总订单数")
    total_amount = Column(Numeric(12, 2), default=0, comment="总金额")
    refund_count = Column(Integer, default=0, comment="退款订单数")
    refund_amount = Column(Numeric(12, 2), default=0, comment="退款金额")
    avg_order_amount = Column(Numeric(12, 2), default=0, comment="平均订单金额")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")

    def __repr__(self):
        return f"<OrderStats(id={self.id}, stat_date='{self.stat_date}')>"
