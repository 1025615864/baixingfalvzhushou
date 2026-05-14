"""账务数据模型"""
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class UserBalance(Base):
    """用户余额表"""
    __tablename__ = "user_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    balance_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_recharged: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_recharged_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_consumed: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_consumed_cents: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<UserBalance(user_id={self.user_id}, balance={self.balance})>"


class BalanceTransaction(Base):
    """余额变动记录表"""
    __tablename__ = "balance_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    order_id: Mapped[int] = mapped_column(Integer, nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # recharge, consume, refund
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_before: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    balance_before_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_tx_user_type", "user_id", "type"),
        Index("idx_tx_created", "created_at"),
        Index("idx_tx_user_created", "user_id", "created_at"),
        Index("idx_tx_order", "order_id"),
    )

    def __repr__(self) -> str:
        return f"<BalanceTransaction(user_id={self.user_id}, type={self.type}, amount={self.amount})>"


class LawyerWallet(Base):
    """律师钱包表"""
    __tablename__ = "lawyer_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    balance_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_income: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_income_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_withdrawn: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_withdrawn_cents: Mapped[int] = mapped_column(Integer, default=0)
    frozen_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    frozen_amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<LawyerWallet(lawyer_id={self.lawyer_id}, balance={self.balance})>"


class Settlement(Base):
    """结算记录表"""
    __tablename__ = "settlements"
    __table_args__ = (
        Index("idx_settlement_lawyer_status", "lawyer_id", "status"),
        Index("idx_settlement_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_fee: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    platform_fee_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    settle_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    settle_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processing, completed, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Settlement(lawyer_id={self.lawyer_id}, amount={self.total_amount}, status={self.status})>"
