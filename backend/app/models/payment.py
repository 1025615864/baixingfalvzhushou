"""支付订单模型"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, Integer, String, Text, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ..database import Base
import enum

if TYPE_CHECKING:
    from .user import User


class RefundStatus(str, enum.Enum):
    """退款状态"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    SUCCESS = "success"  # 退款成功
    FAILED = "failed"  # 退款失败
    REJECTED = "rejected"  # 已拒绝


class PaymentStatus(str, enum.Enum):
    """支付状态"""
    PENDING = "pending"  # 待支付
    PAID = "paid"  # 已支付
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款
    FAILED = "failed"  # 支付失败


class PaymentMethod(str, enum.Enum):
    """支付方式"""
    ALIPAY = "alipay"  # 支付宝
    WECHAT = "wechat"  # 微信支付
    BALANCE = "balance"  # 余额支付
    IKUNPAY = "ikunpay"  # 爱坤支付


class OrderType(str, enum.Enum):
    """订单类型"""
    CONSULTATION = "consultation"  # 律师咨询
    SERVICE = "service"  # 法律服务
    VIP = "vip"  # VIP会员
    RECHARGE = "recharge"  # 余额充值
    LIGHT_CONSULT_REVIEW = "light_consult_review"  # AI咨询律师复核


class PaymentOrder(Base):
    """支付订单表"""
    __tablename__: str = "payment_orders"
    
    # 复合索引优化高频查询
    __table_args__: tuple = (
        # 用户订单列表查询：user_id + created_at 降序
        Index('ix_payment_orders_user_created', 'user_id', 'created_at', postgresql_using='btree'),
        # 状态筛选查询：status + created_at
        Index('ix_payment_orders_status_created', 'status', 'created_at'),
        # 支付方式和状态组合查询
        Index('ix_payment_orders_method_status', 'payment_method', 'status'),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True)  # 订单号
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True)

    order_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 订单类型
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # 订单金额
    actual_amount: Mapped[float] = mapped_column(Float, nullable=False)  # 实付金额
    amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_amount_cents: Mapped[int | None] = mapped_column(
        Integer, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), default=PaymentStatus.PENDING)
    payment_method: Mapped[str | None] = mapped_column(
        String(20), nullable=True)

    # 关联信息
    related_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True)  # 关联ID（如咨询ID）
    related_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True)  # 关联类型

    # 支付信息
    trade_no: Mapped[str | None] = mapped_column(
        String(100), nullable=True)  # 第三方交易号
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)  # 下单IP

    # 订单描述
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)  # 过期时间

    # 关系
    user: Mapped[User] = relationship("User", backref="orders")


class Settlement(Base):
    """结算记录"""
    __tablename__: str = "settlements"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True)

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    user: Mapped[User] = relationship("User", backref="settlements")


class UserBalance(Base):
    """用户余额表"""
    __tablename__: str = "user_balances"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0)  # 可用余额
    frozen: Mapped[float] = mapped_column(Float, default=0.0)  # 冻结金额
    total_recharged: Mapped[float] = mapped_column(Float, default=0.0)  # 累计充值
    total_consumed: Mapped[float] = mapped_column(Float, default=0.0)  # 累计消费
    balance_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frozen_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_recharged_cents: Mapped[int | None] = mapped_column(
        Integer, nullable=True)
    total_consumed_cents: Mapped[int | None] = mapped_column(
        Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    user: Mapped[User] = relationship("User", backref="balance_account")


class BalanceTransaction(Base):
    """余额交易记录表"""
    __tablename__: str = "balance_transactions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True)
    order_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("payment_orders.id"), nullable=True)

    type: Mapped[str] = mapped_column(
        String(20), nullable=False)  # recharge/consume/refund
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # 正数为收入，负数为支出
    balance_before: Mapped[float] = mapped_column(
        Float, nullable=False)  # 交易前余额
    balance_after: Mapped[float] = mapped_column(
        Float, nullable=False)  # 交易后余额
    amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    balance_before_cents: Mapped[int | None] = mapped_column(
        Integer, nullable=True)
    balance_after_cents: Mapped[int | None] = mapped_column(
        Integer, nullable=True)

    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    # 关系
    user: Mapped[User] = relationship("User", backref="balance_transactions")
    order: Mapped[PaymentOrder | None] = relationship(
        "PaymentOrder", backref="transactions")


class PaymentCallbackEvent(Base):
    __tablename__: str = "payment_callback_events"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)

    provider: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True)
    order_no: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True)
    trade_no: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True)

    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)

    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(
        String(200), nullable=True)

    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True)
    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())


class PaymentRefund(Base):
    """退款记录表"""
    __tablename__: str = "payment_refunds"

    __table_args__: tuple = (
        # 订单退款查询索引
        Index('ix_payment_refunds_order_no', 'order_no'),
        # 用户退款列表查询
        Index('ix_payment_refunds_user_created', 'user_id', 'created_at'),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    refund_no: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True)  # 退款单号
    order_no: Mapped[str] = mapped_column(
        String(64), nullable=False)  # 原订单号
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 退款金额
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 退款状态
    status: Mapped[str] = mapped_column(
        String(20), default=RefundStatus.PENDING)

    # 第三方退款单号
    trade_no: Mapped[str | None] = mapped_column(
        String(100), nullable=True)
    refund_trade_no: Mapped[str | None] = mapped_column(
        String(100), nullable=True)  # 第三方退款单号

    # 退款原因
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 处理信息
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    processed_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True)  # 处理人（人工审核时）

    # 失败信息
    error_code: Mapped[str | None] = mapped_column(
        String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(
        String(200), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    user: Mapped[User] = relationship("User", foreign_keys=[user_id], backref="refunds")


class BankCard(Base):
    """银行卡表"""
    __tablename__: str = "bank_cards"

    __table_args__: tuple = (
        # 卡号唯一索引（加密后）
        UniqueConstraint('user_id', 'card_number_encrypted'),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 银行卡信息（敏感信息加密存储）
    card_number_encrypted: Mapped[str] = mapped_column(
        String(255), nullable=False)  # 加密后的完整卡号
    card_number_mask: Mapped[str] = mapped_column(
        String(19), nullable=False)  # 脱敏显示（如 **** **** **** 1234）

    # 卡类型
    card_type: Mapped[str] = mapped_column(
        String(20), nullable=False)  # visa/mastercard/unionpay等
    bank_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True)  # 银行名称

    # 持卡人信息
    cardholder_name: Mapped[str] = mapped_column(
        String(50), nullable=False)
    expiry_month: Mapped[int] = mapped_column(
        Integer, nullable=False)  # 过期月份 1-12
    expiry_year: Mapped[int] = mapped_column(
        Integer, nullable=False)  # 过期年份（如 2026）

    # 状态
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False)  # 是否默认卡
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False)  # 是否已验证
    status: Mapped[str] = mapped_column(
        String(20), default="active")  # active/expired/frozen

    # 安全信息
    billing_address: Mapped[str | None] = mapped_column(
        String(200), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(
            timezone=True),
        server_default=func.now(),
        onupdate=func.now())

    # 关系
    user: Mapped[User] = relationship("User", backref="bank_cards")
