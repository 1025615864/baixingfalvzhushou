"""订单服务 - 订单模型

提供订单管理、订单状态流转、SAGA 事务集成。
"""
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    """订单状态枚举"""

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"


class OrderType(str, enum.Enum):
    """订单类型枚举"""

    LEGAL_CONSULTATION = "legal_consultation"
    DOCUMENT_SERVICE = "document_service"
    MEMBERSHIP = "membership"
    OTHER = "other"


class PaymentMethod(str, enum.Enum):
    """支付方式枚举"""

    ALIPAY = "alipay"
    WECHATPAY = "wechatpay"
    IKUNPAY = "ikunpay"
    BALANCE = "balance"


class Order(Base):
    """订单模型"""

    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_order_user_status", "user_id", "status"),
        Index("idx_order_created", "created_at"),
        Index("idx_order_no", "order_no", unique=True),
        Index("idx_order_saga_id", "saga_id"),
        Index("idx_order_status", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False, comment="订单号")
    user_id = Column(Integer, nullable=False, comment="用户 ID")

    # 订单信息
    order_type = Column(Enum(OrderType), nullable=False, comment="订单类型")
    title = Column(String(255), nullable=False, comment="订单标题")
    description = Column(Text, nullable=True, comment="订单描述")

    # 金额
    amount = Column(Float, nullable=False, comment="订单金额(分)")
    discount_amount = Column(Float, default=0, comment="优惠金额(分)")
    actual_amount = Column(Float, nullable=False, comment="实际支付金额(分)")

    # 状态
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, comment="订单状态")
    payment_method = Column(Enum(PaymentMethod), nullable=True, comment="支付方式")
    payment_time = Column(DateTime, nullable=True, comment="支付时间")

    # SAGA 分布式事务
    saga_id = Column(String(128), nullable=True, comment="Saga 事务 ID")
    saga_status = Column(String(32), nullable=True, comment="Saga 状态")

    # 业务关联
    business_id = Column(Integer, nullable=True, comment="关联业务 ID")
    business_type = Column(String(64), nullable=True, comment="关联业务类型")

    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
    paid_at = Column(DateTime, nullable=True, comment="支付完成时间")
    completed_at = Column(DateTime, nullable=True, comment="订单完成时间")
    cancelled_at = Column(DateTime, nullable=True, comment="订单取消时间")

    # 取消/退款原因
    cancel_reason = Column(String(500), nullable=True, comment="取消原因")
    refund_reason = Column(String(500), nullable=True, comment="退款原因")

    # 扩展信息
    extra = Column(Text, nullable=True, comment="扩展信息(JSON)")

    def __repr__(self):
        return f"<Order(id={self.id}, order_no='{self.order_no}', status='{self.status.value}')>"


class OrderItem(Base):
    """订单明细模型"""

    __tablename__ = "order_items"
    __table_args__ = (
        Index("idx_order_item_order", "order_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False, comment="订单 ID")

    item_name = Column(String(255), nullable=False, comment="商品名称")
    item_description = Column(String(500), nullable=True, comment="商品描述")
    quantity = Column(Integer, default=1, comment="数量")
    unit_price = Column(Float, nullable=False, comment="单价(分)")
    total_price = Column(Float, nullable=False, comment="总价(分)")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, name='{self.item_name}')>"
