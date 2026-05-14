from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Numeric, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class SettlementAudit(Base):
    __tablename__ = "settlement_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    settlement_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    auditor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    auditor_name: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<SettlementAudit(settlement_id={self.settlement_id}, action={self.action})>"


class FinancialReport(Base):
    __tablename__ = "financial_reports"
    __table_args__ = (
        Index("ix_financial_reports_report_date", "report_date", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[str] = mapped_column(String(10), nullable=False, unique=True, index=True)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)
    total_income: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_expense: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    total_profit: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    platform_fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    details_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<FinancialReport(report_date={self.report_date}, type={self.report_type})>"


class AccountingAuditLog(Base):
    __tablename__ = "accounting_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=True)
    operator_id: Mapped[int] = mapped_column(Integer, nullable=False)
    operator_name: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<AccountingAuditLog(operator={self.operator_name}, action={self.action})>"
