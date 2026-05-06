"""法律服务事件 Kafka 生产者"""
import os
import json
import logging
from typing import Optional

try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None

from .legal_events import (
    LegalEvent,
    LegalEventTypes,
    create_legal_event,
)

logger = logging.getLogger(__name__)


class LegalEventBus:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic = "baixing.legal.events"
        self._producer = None
        self._enabled = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}
        self._started = False

    async def start(self):
        if self._producer is None and self._enabled and AIOKafkaProducer:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
            self._started = True
            logger.info("Legal event bus Kafka producer started")

    async def close(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None
            self._started = False
            logger.info("Legal event bus Kafka producer stopped")

    async def publish(self, event: LegalEvent, key: Optional[str] = None):
        if not self._enabled:
            logger.info(f"Kafka disabled, skipping event: {event.event_type}")
            return

        if not self._started:
            await self.start()

        if not self._producer:
            logger.warning("Kafka producer not available")
            return

        try:
            await self._producer.send_and_wait(
                self.topic,
                value=event.to_dict(),
                key=key.encode("utf-8") if key else None,
                headers=[("event_type", event.event_type.encode("utf-8"))],
            )
            logger.info(f"Published event: {event.event_type} with key: {key}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    async def publish_consultation_created(self, consultation):
        event = create_legal_event(
            event_type=LegalEventTypes.CONSULTATION_CREATED,
            consultation_id=str(consultation.id),
            user_id=str(consultation.user_id),
            payload={
                "category": consultation.category,
                "title": consultation.title,
            }
        )
        await self.publish(event, key=str(consultation.id))

    async def publish_consultation_assigned(self, consultation, lawyer_id: int):
        event = create_legal_event(
            event_type=LegalEventTypes.CONSULTATION_ASSIGNED,
            consultation_id=str(consultation.id),
            lawyer_id=str(lawyer_id),
            user_id=str(consultation.user_id),
            payload={"status": consultation.status}
        )
        await self.publish(event, key=str(consultation.id))

    async def publish_consultation_completed(self, consultation):
        event = create_legal_event(
            event_type=LegalEventTypes.CONSULTATION_COMPLETED,
            consultation_id=str(consultation.id),
            lawyer_id=str(consultation.lawyer_id) if consultation.lawyer_id else None,
            user_id=str(consultation.user_id),
            payload={"status": consultation.status}
        )
        await self.publish(event, key=str(consultation.id))

    async def publish_consultation_cancelled(self, consultation):
        event = create_legal_event(
            event_type=LegalEventTypes.CONSULTATION_CANCELLED,
            consultation_id=str(consultation.id),
            user_id=str(consultation.user_id),
            payload={"status": consultation.status}
        )
        await self.publish(event, key=str(consultation.id))

    async def publish_lawyer_verified(self, lawyer):
        event = create_legal_event(
            event_type=LegalEventTypes.LAWYER_VERIFIED,
            lawyer_id=str(lawyer.id),
            user_id=str(lawyer.user_id),
            payload={"name": lawyer.name, "status": lawyer.status}
        )
        await self.publish(event, key=str(lawyer.id))

    async def publish_lawyer_rating_updated(self, lawyer, new_rating: float):
        event = create_legal_event(
            event_type=LegalEventTypes.LAWYER_RATING_UPDATED,
            lawyer_id=str(lawyer.id),
            payload={
                "old_rating": lawyer.rating,
                "new_rating": new_rating,
            }
        )
        await self.publish(event, key=str(lawyer.id))

    async def publish_review_submitted(self, consultation_id: int, lawyer_id: int, rating: int):
        event = create_legal_event(
            event_type=LegalEventTypes.REVIEW_SUBMITTED,
            consultation_id=str(consultation_id),
            lawyer_id=str(lawyer_id),
            payload={"rating": rating}
        )
        await self.publish(event, key=str(consultation_id))


event_bus = LegalEventBus()