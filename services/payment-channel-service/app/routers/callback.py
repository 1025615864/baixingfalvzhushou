"""支付回调路由"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import PaymentOrder, PaymentCallback
from ..services.idempotency_service import IdempotencyService
from ..services.payment_service import PaymentService

try:
    from ..events.kafka_client import get_publisher
    from ..events.kafka_events import PaymentCompletedEvent
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False
    get_publisher = None
    PaymentCompletedEvent = None

logger = logging.getLogger(__name__)
router = APIRouter()
payment_service = PaymentService()


@router.post("/alipay")
async def alipay_callback(
    request: Request,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """支付宝回调"""
    payload = await request.json()

    order_no = payload.get("out_trade_no")
    trade_no = payload.get("trade_no")
    status = payload.get("trade_status")

    idempotency = IdempotencyService(db)
    if await idempotency.is_processed("alipay", order_no):
        return {"success": True, "message": "Already processed"}

    normalized_status = "success" if status == "TRADE_SUCCESS" else status
    order = await payment_service.process_callback(
        db=db,
        order_no=order_no,
        provider="alipay",
        callback_no=trade_no,
        status=normalized_status,
        raw_payload=payload,
    )

    if normalized_status == "success" and order.status == "paid":
        try:
            if HAS_KAFKA and get_publisher:
                publisher = await get_publisher()
                if publisher:
                    event = PaymentCompletedEvent(
                        order_id=order.order_no,
                        user_id=order.user_id,
                        amount=float(order.amount),
                        payment_method="alipay",
                        trade_no=trade_no,
                    )
                    await publisher.publish(event, key=str(order.user_id))
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    await db.commit()
    await idempotency.mark_processed("alipay", order_no)

    return {"success": True}


@router.post("/wechat")
async def wechatpay_callback(
    request: Request,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """微信支付回调"""
    payload = await request.json()

    order_no = payload.get("out_trade_no")
    transaction_id = payload.get("transaction_id")
    status = payload.get("trade_state")

    idempotency = IdempotencyService(db)
    if await idempotency.is_processed("wechat", order_no):
        return {"success": True, "message": "Already processed"}

    normalized_status = "success" if status == "SUCCESS" else status
    order = await payment_service.process_callback(
        db=db,
        order_no=order_no,
        provider="wechat",
        callback_no=transaction_id,
        status=normalized_status,
        raw_payload=payload,
    )

    if normalized_status == "success" and order.status == "paid":
        try:
            if HAS_KAFKA and get_publisher:
                publisher = await get_publisher()
                if publisher:
                    event = PaymentCompletedEvent(
                        order_id=order.order_no,
                        user_id=order.user_id,
                        amount=float(order.amount),
                        payment_method="wechatpay",
                        trade_no=transaction_id,
                    )
                    await publisher.publish(event, key=str(order.user_id))
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    await db.commit()
    await idempotency.mark_processed("wechat", order_no)

    return {"success": True}
