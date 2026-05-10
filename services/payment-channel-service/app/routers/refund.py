import logging
import secrets
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import PaymentOrder, PaymentRefund
from ..services.channels import get_adapter

logger = logging.getLogger(__name__)
router = APIRouter()


class RefundRequest(BaseModel):
    amount: Optional[float] = None
    reason: str = ""


class RefundResponse(BaseModel):
    id: int
    order_no: str
    refund_no: str
    amount: float
    reason: str
    status: str
    provider: str
    created_at: datetime

    class Config:
        from_attributes = True


def generate_refund_no() -> str:
    now = datetime.now()
    random_part = secrets.token_hex(4).upper()
    return f"REF{now.strftime('%Y%m%d')}{random_part}"


@router.post("/orders/{order_no}/refund", response_model=RefundResponse)
async def initiate_refund(
    order_no: str,
    request: RefundRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == order_no)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "paid":
        raise HTTPException(status_code=400, detail="Only paid orders can be refunded")

    refund_amount = request.amount if request.amount else float(order.amount)
    refund_amount_cents = int(refund_amount * 100)

    if refund_amount_cents > order.amount_cents:
        raise HTTPException(status_code=400, detail="Refund amount exceeds order amount")

    existing_refund_result = await db.execute(
        select(PaymentRefund).where(
            PaymentRefund.order_no == order_no,
            PaymentRefund.status.in_(["pending", "processing"]),
        )
    )
    existing_refund = existing_refund_result.scalar_one_or_none()
    if existing_refund:
        raise HTTPException(status_code=400, detail="A pending refund already exists for this order")

    refund_no = generate_refund_no()
    provider = order.payment_method or "alipay"

    try:
        adapter = get_adapter(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported payment provider: {provider}")

    refund_record = PaymentRefund(
        order_no=order_no,
        refund_no=refund_no,
        amount=refund_amount,
        reason=request.reason,
        status="processing",
        provider=provider,
    )
    db.add(refund_record)
    await db.commit()
    await db.refresh(refund_record)

    try:
        refund_result = await adapter.refund(
            order_no=order_no,
            refund_no=refund_no,
            amount=refund_amount_cents,
            total_amount=order.amount_cents,
            reason=request.reason,
        )

        if refund_result.get("success"):
            refund_record.status = "success"
            refund_record.provider_refund_no = refund_result.get("provider_refund_no", "")
            refund_record.completed_at = datetime.now()
            order.status = "refunded"
        else:
            refund_record.status = "failed"
    except Exception as e:
        logger.error(f"Refund failed for order {order_no}: {e}")
        refund_record.status = "failed"

    await db.commit()
    await db.refresh(refund_record)

    return RefundResponse.model_validate(refund_record)


@router.post("/refund/{provider}")
async def refund_callback(
    provider: str,
    request: dict,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal()),
):
    try:
        adapter = get_adapter(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported payment provider: {provider}")

    is_valid = await adapter.verify_callback(request)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid callback signature")

    if provider == "alipay":
        refund_no = request.get("out_request_no", "")
        refund_status = request.get("refund_status", "")
        provider_refund_no = request.get("trade_no", "")
    elif provider == "wechat":
        refund_no = request.get("out_refund_no", "")
        refund_status = request.get("refund_status", "")
        provider_refund_no = request.get("refund_id", "")
    else:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    if not refund_no:
        raise HTTPException(status_code=400, detail="Missing refund number in callback")

    result = await db.execute(
        select(PaymentRefund).where(PaymentRefund.refund_no == refund_no)
    )
    refund_record = result.scalar_one_or_none()

    if not refund_record:
        raise HTTPException(status_code=404, detail="Refund record not found")

    if refund_record.status in ("success", "failed"):
        return {"success": True, "message": "Already processed"}

    if refund_status in ("REFUND_SUCCESS", "SUCCESS"):
        refund_record.status = "success"
        refund_record.provider_refund_no = provider_refund_no
        refund_record.completed_at = datetime.now()

        order_result = await db.execute(
            select(PaymentOrder).where(PaymentOrder.order_no == refund_record.order_no)
        )
        order = order_result.scalar_one_or_none()
        if order:
            order.status = "refunded"
    elif refund_status in ("REFUND_FAIL", "FAIL", "FAILED", "CHANGE"):
        refund_record.status = "failed"

    await db.commit()

    return {"success": True}
