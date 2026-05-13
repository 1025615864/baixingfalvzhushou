import logging
from typing import Optional

try:
    from services.common.events.kafka_events import OrderEvent, OrderEventTypes
    from services.common.events.producer import get_event_bus
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False
    OrderEvent = None
    OrderEventTypes = None
    get_event_bus = None

logger = logging.getLogger(__name__)


class OrderEventPublisher:
    def __init__(self):
        self._event_bus = None

    async def _get_bus(self):
        if not HAS_KAFKA:
            return None
        if self._event_bus is None:
            self._event_bus = get_event_bus()
        return self._event_bus

    async def publish_order_created(self, order) -> bool:
        bus = await self._get_bus()
        if not bus:
            logger.warning("Kafka not available, skipping publish_order_created")
            return False
        event = OrderEvent(
            event_type=OrderEventTypes.ORDER_CREATED,
            order_id=str(order.id),
            user_id=str(order.user_id),
            amount=int(order.actual_amount * 100),
            status=order.status.value,
            items=[],
            source="order-service",
        )
        return await bus.publish_order_event(event, str(order.id))

    async def publish_order_paid(self, order) -> bool:
        bus = await self._get_bus()
        if not bus:
            logger.warning("Kafka not available, skipping publish_order_paid")
            return False
        event = OrderEvent(
            event_type=OrderEventTypes.ORDER_PAID,
            order_id=str(order.id),
            user_id=str(order.user_id),
            amount=int(order.actual_amount * 100),
            status=order.status.value,
            items=[],
            source="order-service",
        )
        return await bus.publish_order_event(event, str(order.id))

    async def publish_order_cancelled(self, order) -> bool:
        bus = await self._get_bus()
        if not bus:
            logger.warning("Kafka not available, skipping publish_order_cancelled")
            return False
        event = OrderEvent(
            event_type=OrderEventTypes.ORDER_CANCELLED,
            order_id=str(order.id),
            user_id=str(order.user_id),
            amount=int(order.actual_amount * 100),
            status=order.status.value,
            items=[],
            source="order-service",
        )
        return await bus.publish_order_event(event, str(order.id))

    async def publish_order_completed(self, order) -> bool:
        bus = await self._get_bus()
        if not bus:
            logger.warning("Kafka not available, skipping publish_order_completed")
            return False
        event = OrderEvent(
            event_type=OrderEventTypes.ORDER_COMPLETED,
            order_id=str(order.id),
            user_id=str(order.user_id),
            amount=int(order.actual_amount * 100),
            status=order.status.value,
            items=[],
            source="order-service",
        )
        return await bus.publish_order_event(event, str(order.id))

    async def publish_order_refunded(self, order) -> bool:
        bus = await self._get_bus()
        if not bus:
            logger.warning("Kafka not available, skipping publish_order_refunded")
            return False
        event = OrderEvent(
            event_type="order.refunded",
            order_id=str(order.id),
            user_id=str(order.user_id),
            amount=int(order.actual_amount * 100),
            status=order.status.value,
            items=[],
            source="order-service",
        )
        return await bus.publish_order_event(event, str(order.id))


order_event_publisher = OrderEventPublisher()
