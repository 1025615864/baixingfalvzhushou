"""支付回调路由"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import PaymentOrder, PaymentCallback
from ..services.idempotency_service import IdempotencyService

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


@router.post("/alipay")
async def alipay_callback(
    request: Request,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """支付宝回调"""
    # 获取回调数据
    payload = await request.json()

    order_no = payload.get("out_trade_no")
    trade_no = payload.get("trade_no")
    status = payload.get("trade_status")

    # 幂等检查
    idempotency = IdempotencyService(db)
    if await idempotency.is_processed("alipay", order_no):
        return {"success": True, "message": "Already processed"}

    # 记录回调
    callback = PaymentCallback(
        order_no=order_no,
        provider="alipay",
        callback_no=trade_no,
        status=status,
        raw_payload=str(payload),
    )
    db.add(callback)

    # 更新订单状态
    if status == "TRADE_SUCCESS":
        result = await db.execute(
            PaymentOrder.__table__.select().where(PaymentOrder.order_no == order_no)
        )
        order = result.fetchone()
        if order:
            order.status = "paid"
            order.trade_no = trade_no
            order.paid_at = datetime.now()

            # 发布支付完成事件
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

    # 标记为已处理
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

    # 幂等检查
    idempotency = IdempotencyService(db)
    if await idempotency.is_processed("wechat", order_no):
        return {"success": True, "message": "Already processed"}

    # 记录回调
    callback = PaymentCallback(
        order_no=order_no,
        provider="wechat",
        callback_no=transaction_id,
        status=status,
        raw_payload=str(payload),
    )
    db.add(callback)

    # 更新订单状态
    if status == "SUCCESS":
        result = await db.execute(
            PaymentOrder.__table__.select().where(PaymentOrder.order_no == order_no)
        )
        order = result.fetchone()
        if order:
            order.status = "paid"
            order.trade_no = transaction_id
            order.paid_at = datetime.now()

            # 发布支付完成事件
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

    # 标记为已处理
    await idempotency.mark_processed("wechat", order_no)

    return {"success": True}
