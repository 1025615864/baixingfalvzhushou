"""支付通道数据模型"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class PaymentOrder(Base):
    """支付订单表"""
    __tablename__ = "payment_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    order_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    actual_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    trade_no: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    related_id: Mapped[int] = mapped_column(Integer, nullable=True)
    related_type: Mapped[str] = mapped_column(String(50), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_orders_user_status", "user_id", "status"),
        Index("idx_orders_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PaymentOrder(order_no={self.order_no}, amount={self.amount}, status={self.status})>"


class PaymentCallback(Base):
    """支付回调记录表"""
    __tablename__ = "payment_callbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    callback_no: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<PaymentCallback(order_no={self.order_no}, provider={self.provider}, status={self.status})>"


class PaymentRefund(Base):
    __tablename__ = "payment_refunds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    refund_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_refund_no: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_refunds_order_status", "order_no", "status"),
    )

    def __repr__(self) -> str:
        return f"<PaymentRefund(refund_no={self.refund_no}, order_no={self.order_no}, status={self.status})>"
