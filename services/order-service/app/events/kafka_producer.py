import logging
import os
from typing import Optional

try:
    from services.common.events import (
        EventBus,
        OrderEvent,
        OrderEventTypes,
        init_event_bus,
        close_event_bus,
    )
except ImportError:
    EventBus = None
    OrderEvent = None
    OrderEventTypes = None
    init_event_bus = None
    close_event_bus = None

logger = logging.getLogger(__name__)

_event_bus: Optional[EventBus] = None


async def init_kafka_producer(bootstrap_servers: str = "kafka:29092"):
    global _event_bus
    if init_event_bus is None:
        logger.warning("services.common.events not available, Kafka producer disabled")
        return None
    _event_bus = await init_event_bus(bootstrap_servers)
    logger.info(f"Order service Kafka producer initialized: {bootstrap_servers}")
    return _event_bus


async def close_kafka_producer():
    global _event_bus
    if _event_bus:
        if close_event_bus is not None:
            await close_event_bus()
        _event_bus = None
        logger.info("Order service Kafka producer closed")


class EventPublisher:
    def __init__(self):
        self._producer = None

    async def publish(self, event_type: str, payload) -> bool:
        if not _event_bus:
            logger.warning("Kafka producer not initialized, event dropped")
            return False
        try:
            from services.common.events.kafka_events import BaseEvent
            import uuid
            from datetime import datetime

            if isinstance(payload, dict):
                event = BaseEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=event_type,
                    timestamp=datetime.utcnow().isoformat(),
                    version="1.0",
                    source="order-service",
                )
            else:
                event = payload

            topic = _event_bus.get_topic("order")
            await _event_bus.producer.send(topic, event, key=str(uuid.uuid4()))
            logger.info(f"Published event: {event_type} to {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False


event_publisher = EventPublisher()
