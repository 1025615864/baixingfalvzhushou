import logging
from typing import Optional

from services.common.events.kafka_events import OrderEvent, OrderEventTypes
from services.common.events.producer import get_event_bus

logger = logging.getLogger(__name__)


class OrderEventPublisher:
    def __init__(self):
        self._event_bus = None

    async def _get_bus(self):
        if self._event_bus is None:
            self._event_bus = get_event_bus()
        return self._event_bus

    async def publish_order_created(self, order) -> bool:
        bus = await self._get_bus()
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
