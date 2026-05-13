import asyncio
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_consumer_task: Optional[asyncio.Task] = None
_consumer = None


async def init_kafka_consumer(bootstrap_servers: str = "kafka:29092"):
    global _consumer, _consumer_task
    try:
        from aiokafka import AIOKafkaConsumer

        topics = [
            "baixing.order.events",
            "baixing.payment.events",
            "baixing.user.events",
        ]

        _consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id="notification-service-consumer",
            value_deserializer=lambda v: json.loads(v.decode()),
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        await _consumer.start()
        _consumer_task = asyncio.create_task(_consume_loop())
        logger.info(f"Notification service Kafka consumer started: {bootstrap_servers}")
    except ImportError:
        logger.warning("aiokafka not installed, Kafka consumer disabled")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumer: {e}")


async def _consume_loop():
    if not _consumer:
        return
    try:
        async for message in _consumer:
            try:
                await _handle_message(message)
            except Exception as e:
                logger.error(f"Error handling Kafka message: {e}")
    except asyncio.CancelledError:
        logger.info("Kafka consumer cancelled")
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}")


async def _handle_message(message):
    from app.services.notification_service import NotificationService
    from app.database import async_session_factory

    value = message.value
    event_type = value.get("event_type", "")
    logger.info(f"Received Kafka event: {event_type}")

    notifications = {
        "order.paid": ("order", "订单支付成功", "您的订单已支付成功"),
        "order.cancelled": ("order", "订单已取消", "您的订单已取消"),
        "order.completed": ("order", "订单已完成", "您的订单已完成"),
        "payment.success": ("payment", "支付成功", "您的支付已成功处理"),
        "payment.failed": ("payment", "支付失败", "您的支付处理失败，请重试"),
        "payment.refunded": ("payment", "退款成功", "您的退款已成功处理"),
        "user.membership_activated": ("system", "会员激活", "您的会员已成功激活"),
    }

    if event_type not in notifications:
        return

    ntype, title, body = notifications[event_type]
    user_id = value.get("user_id")

    if not user_id:
        return

    async with async_session_factory() as session:
        service = NotificationService(session)
        await service.create_notification(
            user_id=user_id,
            notification_type=ntype,
            title=title,
            body=body,
            data=value,
        )


async def close_kafka_consumer():
    global _consumer, _consumer_task
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
        _consumer_task = None
    if _consumer:
        await _consumer.stop()
        _consumer = None
    logger.info("Notification service Kafka consumer closed")
