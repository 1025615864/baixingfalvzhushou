"""Payment Channel Service Kafka 事件发布"""

import logging
from typing import Optional

from .payment_events import (
    PaymentEventBus,
    PaymentEvent,
    PaymentEventTypes,
    create_payment_event,
)
from services.common.events import (
    init_event_bus,
    close_event_bus,
)

logger = logging.getLogger(__name__)

_event_bus: Optional[PaymentEventBus] = None


async def init_kafka_producer(bootstrap_servers: str = "kafka:9092"):
    """初始化 Kafka 生产者"""
    global _event_bus
    event_bus = await init_event_bus(bootstrap_servers)
    _event_bus = PaymentEventBus(event_bus._producer)
    logger.info(f"Payment channel service Kafka producer initialized: {bootstrap_servers}")
    return _event_bus


async def close_kafka_producer():
    """关闭 Kafka 生产者"""
    global _event_bus
    if _event_bus:
        await close_event_bus()
        _event_bus = None
        logger.info("Payment channel service Kafka producer closed")


async def publish_payment_completed(
    order_id: str,
    payment_id: str,
    user_id: str,
    amount: int,
) -> bool:
    """发布支付完成事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_payment_event(
        event_type=PaymentEventTypes.PAYMENT_COMPLETED,
        order_id=order_id,
        payment_id=payment_id,
        user_id=user_id,
        amount=amount,
        source="payment-channel-service",
    )

    try:
        await _event_bus.publish_order_event(event, order_id)
        logger.info(f"Published payment.completed event: {payment_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish payment.completed event: {e}")
        return False


async def publish_payment_failed(
    order_id: str,
    user_id: str,
    error: str,
) -> bool:
    """发布支付失败事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_payment_event(
        event_type=PaymentEventTypes.PAYMENT_FAILED,
        order_id=order_id,
        user_id=user_id,
        payload={"error": error},
        source="payment-channel-service",
    )

    try:
        await _event_bus.publish_order_event(event, order_id)
        logger.info(f"Published payment.failed event for order: {order_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish payment.failed event: {e}")
        return False
