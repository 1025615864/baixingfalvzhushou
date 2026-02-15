"""收入记录服务模块

包含：
- IncomeService: 收入记录管理（创建、结算）
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.lawfirm import LawyerConsultation
from ...models.payment import PaymentOrder, PaymentStatus
from ...models.settlement import LawyerIncomeRecord

from .core import (
    SettlementService,
    _now,
    _quantize_amount,
    _decimal_to_cents,
    _recalc_wallet_fields,
)


class IncomeService:
    """收入记录服务"""

    def __init__(self, settlement_service: SettlementService):
        self._settlement = settlement_service

    async def ensure_income_record_for_completed_consultation(
        self,
        db: AsyncSession,
        consultation: LawyerConsultation,
        order: PaymentOrder | None,
    ) -> LawyerIncomeRecord | None:
        """确保咨询完成后的收入记录"""
        if order is None:
            return None
        status_value = getattr(order, "status", None)
        if isinstance(status_value, PaymentStatus):
            status_value = status_value.value
        if str(status_value or "").lower() != str(PaymentStatus.PAID.value).lower():
            return None

        res = await db.execute(
            select(LawyerIncomeRecord).where(
                LawyerIncomeRecord.consultation_id == int(consultation.id),
                LawyerIncomeRecord.lawyer_id == int(consultation.lawyer_id),
            )
        )
        existing = res.scalar_one_or_none()
        if existing is not None:
            return existing

        paid_amount = _quantize_amount(float(order.actual_amount or 0.0))
        platform_fee_rate = await self._settlement.get_platform_fee_rate(db, int(consultation.lawyer_id))
        if platform_fee_rate < 0:
            platform_fee_rate = 0.0
        if platform_fee_rate > 1:
            platform_fee_rate = 1.0

        platform_fee = (
            paid_amount *
            Decimal(
                str(platform_fee_rate))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP)
        if platform_fee < Decimal("0"):
            platform_fee = Decimal("0")
        if platform_fee > paid_amount:
            platform_fee = paid_amount
        lawyer_income = paid_amount - platform_fee

        # 根据律师等级获取冻结期天数
        freeze_days = await self._settlement.get_freeze_days(db, int(consultation.lawyer_id))
        settle_time = _now() + timedelta(days=int(freeze_days))

        record = LawyerIncomeRecord(
            lawyer_id=int(consultation.lawyer_id),
            consultation_id=int(consultation.id),
            order_no=str(order.order_no or "").strip() or None,
            user_paid_amount=float(paid_amount),
            platform_fee=float(platform_fee),
            lawyer_income=float(lawyer_income),
            user_paid_amount_cents=_decimal_to_cents(paid_amount),
            platform_fee_cents=_decimal_to_cents(platform_fee),
            lawyer_income_cents=_decimal_to_cents(lawyer_income),
            withdrawn_amount=0.0,
            withdrawn_amount_cents=0,
            status="pending",
            settle_time=settle_time,
        )
        db.add(record)

        wallet = await self._settlement.get_or_create_wallet(db, int(consultation.lawyer_id))
        wallet.total_income = float(
            _quantize_amount(
                float(
                    wallet.total_income or 0.0)) +
            lawyer_income)
        wallet.pending_amount = float(
            _quantize_amount(
                float(
                    wallet.pending_amount or 0.0)) +
            lawyer_income)
        _recalc_wallet_fields(wallet)
        db.add(wallet)

        await db.commit()
        await db.refresh(record)
        return record

    async def ensure_income_record_for_paid_review_order(
        self,
        db: AsyncSession,
        *,
        lawyer_id: int,
        order: PaymentOrder,
    ) -> LawyerIncomeRecord | None:
        """确保已支付审核订单的收入记录"""
        status_value = getattr(order, "status", None)
        if isinstance(status_value, PaymentStatus):
            status_value = status_value.value
        if str(status_value or "").lower() != str(PaymentStatus.PAID.value).lower():
            return None

        order_type_value = getattr(order, "order_type", "")
        if hasattr(order_type_value, "value"):
            order_type_value = getattr(order_type_value, "value")
        if str(order_type_value or "").lower() != "light_consult_review":
            return None

        order_no = str(getattr(order, "order_no", "") or "").strip() or None
        if order_no is None:
            return None

        res = await db.execute(
            select(LawyerIncomeRecord).where(
                LawyerIncomeRecord.lawyer_id == int(lawyer_id),
                LawyerIncomeRecord.order_no == order_no,
            )
        )
        existing = res.scalar_one_or_none()
        if existing is not None:
            return existing

        paid_amount = _quantize_amount(float(order.actual_amount or 0.0))

        platform_fee_rate = await self._settlement.get_platform_fee_rate(db, int(lawyer_id))
        if platform_fee_rate < 0:
            platform_fee_rate = 0.0
        if platform_fee_rate > 1:
            platform_fee_rate = 1.0

        platform_fee = (
            paid_amount *
            Decimal(
                str(platform_fee_rate))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP)
        if platform_fee < Decimal("0"):
            platform_fee = Decimal("0")
        if platform_fee > paid_amount:
            platform_fee = paid_amount
        lawyer_income = paid_amount - platform_fee

        # 根据律师等级获取冻结期天数
        freeze_days = await self._settlement.get_freeze_days(db, int(lawyer_id))
        settle_time = _now() + timedelta(days=int(freeze_days))

        record = LawyerIncomeRecord(
            lawyer_id=int(lawyer_id),
            consultation_id=None,
            order_no=order_no,
            user_paid_amount=float(paid_amount),
            platform_fee=float(platform_fee),
            lawyer_income=float(lawyer_income),
            user_paid_amount_cents=_decimal_to_cents(paid_amount),
            platform_fee_cents=_decimal_to_cents(platform_fee),
            lawyer_income_cents=_decimal_to_cents(lawyer_income),
            withdrawn_amount=0.0,
            withdrawn_amount_cents=0,
            status="pending",
            settle_time=settle_time,
        )
        db.add(record)

        wallet = await self._settlement.get_or_create_wallet(db, int(lawyer_id))
        wallet.total_income = float(
            _quantize_amount(
                float(
                    wallet.total_income or 0.0)) +
            lawyer_income)
        wallet.pending_amount = float(
            _quantize_amount(
                float(
                    wallet.pending_amount or 0.0)) +
            lawyer_income)
        _recalc_wallet_fields(wallet)
        db.add(wallet)

        await db.commit()
        await db.refresh(record)
        return record

    async def settle_due_income_records(
            self, db: AsyncSession) -> dict[str, int]:
        """结算到期的收入记录"""
        now = _now()
        res = await db.execute(
            select(LawyerIncomeRecord).where(
                LawyerIncomeRecord.status == "pending",
                LawyerIncomeRecord.settle_time.is_not(None),
                LawyerIncomeRecord.settle_time <= now,
            )
        )
        records = res.scalars().all()
        settled = 0

        for r in records:
            amount = _quantize_amount(float(r.lawyer_income or 0.0))
            if amount <= Decimal("0"):
                r.status = "settled"
                db.add(r)
                settled += 1
                continue

            wallet = await self._settlement.get_or_create_wallet(db, int(r.lawyer_id))
            wallet.pending_amount = float(_quantize_amount(
                float(wallet.pending_amount or 0.0)) - amount)
            if float(wallet.pending_amount) < 0:
                wallet.pending_amount = 0.0
            _recalc_wallet_fields(wallet)

            r.status = "settled"
            db.add_all([wallet, r])
            settled += 1

        await db.commit()
        return {"settled": int(settled)}
