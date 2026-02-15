from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import Integer, cast as sa_cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.payment import PaymentOrder, PaymentStatus
from ...models.user import User
from ...utils.deps import require_admin

router = APIRouter()


@router.get("/admin/stats", summary="管理员-支付统计")
async def admin_payment_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """支付统计数据"""
    _ = current_user
    total_orders = await db.scalar(select(func.count()).select_from(PaymentOrder)) or 0

    paid_orders = (
        await db.scalar(select(func.count()).select_from(PaymentOrder).where(PaymentOrder.status == PaymentStatus.PAID))
        or 0
    )

    total_revenue_cents = (
        await db.scalar(
            select(
                func.sum(
                    func.coalesce(
                        PaymentOrder.actual_amount_cents,
                        sa_cast(
                            func.round(
                                PaymentOrder.actual_amount *
                                100),
                            Integer),
                    )
                )
            ).where(PaymentOrder.status == PaymentStatus.PAID)
        )
        or 0
    )
    total_revenue = float(
        (Decimal(
            int(total_revenue_cents)) /
            100).quantize(
            Decimal("0.01")))

    today = datetime.now(timezone.utc).date()
    today_revenue_cents = (
        await db.scalar(
            select(
                func.sum(
                    func.coalesce(
                        PaymentOrder.actual_amount_cents,
                        sa_cast(
                            func.round(
                                PaymentOrder.actual_amount *
                                100),
                            Integer),
                    )
                )
            ).where(
                PaymentOrder.status == PaymentStatus.PAID,
                func.date(PaymentOrder.paid_at) == today,
            )
        )
        or 0
    )
    today_revenue = float(
        (Decimal(
            int(today_revenue_cents)) /
            100).quantize(
            Decimal("0.01")))

    return {
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "total_revenue": total_revenue,
        "today_revenue": today_revenue,
        "conversion_rate": round(paid_orders / max(total_orders, 1) * 100, 1),
    }
