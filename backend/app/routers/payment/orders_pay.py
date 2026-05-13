from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.config import get_settings
from app.utils.deps import get_current_user, require_admin
from app.models.user import User
from app.models.payment import PaymentOrder, PaymentStatus, PaymentMethod
from app.services.payment_service import payment_service
from app.routers.payment import legacy

router = APIRouter()

prometheus_metrics = legacy.prometheus_metrics if hasattr(legacy, "prometheus_metrics") else None


class PayOrderRequest(BaseModel):
    payment_method: str = "alipay"


@router.post("/orders/{order_no}/pay")
async def pay_order(
    order_no: str,
    data: PayOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    legacy.prometheus_metrics = prometheus_metrics
    return await legacy.pay_order(order_no, data, current_user, db)


@router.get("/admin/orders")
async def admin_get_orders(
    page: int = 1,
    page_size: int = 10,
    status_filter: str | None = None,
    user_id: int | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    orders, total = await payment_service.admin_get_orders(
        db, page=page, page_size=page_size, status_filter=status_filter, user_id=user_id,
    )
    items = []
    for o in orders:
        items.append({
            "id": o.id, "order_no": o.order_no, "user_id": o.user_id,
            "order_type": o.order_type, "amount": float(o.amount) if o.amount else 0,
            "actual_amount": float(o.actual_amount) if o.actual_amount else 0,
            "status": o.status, "title": o.title,
            "payment_method": o.payment_method,
            "created_at": str(o.created_at) if o.created_at else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/admin/refund/{order_no}")
async def admin_refund(
    order_no: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        order = await payment_service.admin_refund(db, order_no=order_no)
        return {"ok": True, "message": "退款成功", "order_no": order.order_no}
    except ValueError as e:
        err_msg = str(e)
        if "不存在" in err_msg:
            return JSONResponse(status_code=404, content={"ok": False, "error": err_msg})
        return JSONResponse(status_code=400, content={"ok": False, "error": err_msg})


@router.post("/admin/orders/{order_no}/mark-paid")
async def admin_mark_paid(
    order_no: str,
    data: dict,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    payment_method = data.get("payment_method", "alipay")
    try:
        stmt = select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing and existing.status == PaymentStatus.PAID.value:
            return {"ok": True, "message": "订单已是支付成功状态", "order_no": order_no}
        order = await payment_service.mark_order_paid(db, order_no=order_no, payment_method=payment_method)
        return {"ok": True, "message": "标记成功", "order_no": order.order_no}
    except ValueError as e:
        err_msg = str(e)
        return JSONResponse(status_code=400, content={"ok": False, "error": err_msg})


@router.get("/admin/callback-events")
async def admin_callback_events(
    page: int = 1,
    page_size: int = 10,
    order_no: str | None = None,
    verified: bool | None = None,
    provider: str | None = None,
    has_error: bool | None = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    events, total = await payment_service.get_callback_events(
        db, page=page, page_size=page_size, order_no=order_no, verified=verified,
        provider=provider, has_error=has_error,
    )
    items = []
    for e in events:
        items.append({
            "id": e.id, "provider": e.provider, "order_no": e.order_no,
            "trade_no": e.trade_no, "amount": e.amount,
            "verified": e.verified, "error_message": e.error_message,
            "created_at": str(e.created_at) if e.created_at else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}
