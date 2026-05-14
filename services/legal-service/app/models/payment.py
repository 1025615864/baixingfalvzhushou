from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ConsultationPayment(Base):
    __tablename__ = "consultation_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consultation_id: Mapped[int] = mapped_column(Integer, ForeignKey("consultations.id"), nullable=False, index=True)
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    platform_fee_rate: Mapped[float] = mapped_column(Float, default=0.15)
    platform_fee: Mapped[float] = mapped_column(Float, default=0.0)
    lawyer_income: Mapped[float] = mapped_column(Float, default=0.0)
    pay_method: Mapped[str] = mapped_column(String(20), default="wechat")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<ConsultationPayment(id={self.id}, order_no={self.order_no}, status={self.status})>"


class LawyerWallet(Base):
    __tablename__ = "lawyer_wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("lawyers.id"), nullable=False, unique=True, index=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    frozen_balance: Mapped[float] = mapped_column(Float, default=0.0)
    total_income: Mapped[float] = mapped_column(Float, default=0.0)
    total_withdrawn: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<LawyerWallet(id={self.id}, lawyer_id={self.lawyer_id}, balance={self.balance})>"


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_id: Mapped[int] = mapped_column(Integer, ForeignKey("lawyer_wallets.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, default=0.0)
    order_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("consultation_payments.id"), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<WalletTransaction(id={self.id}, wallet_id={self.wallet_id}, type={self.type}, amount={self.amount})>"