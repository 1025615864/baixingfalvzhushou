import asyncio
import logging
from typing import Optional, Dict, List
from aiokafka import AIOKafkaProducer
from .kafka_events import BaseEvent

logger = logging.getLogger(__name__)


class KafkaProducerClient:
    def __init__(
        self,
        bootstrap_servers: str,
        client_id: str = "baixing-producer",
        acks: str = "all",
        enable_idempotence: bool = True,
    ):
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.acks = acks
        self.enable_idempotence = enable_idempotence
        self._producer: Optional[AIOKafkaProducer] = None
        self._started = False

    async def start(self):
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                client_id=self.client_id,
                bootstrap_servers=self.bootstrap_servers,
                acks=self.acks,
                enable_idempotence=self.enable_idempotence,
                max_batch_size=16384,
                linger_ms=10,
                compression_type="gzip",
            )
            await self._producer.start()
            self._started = True
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None
            self._started = False
            logger.info("Kafka producer stopped")

    async def send(
        self,
        topic: str,
        event: BaseEvent,
        key: Optional[str] = None,
        headers: Optional[List[tuple]] = None,
    ) -> bool:
        if not self._started:
            await self.start()

        if headers is None:
            headers = [("event_type", event.event_type.encode("utf-8"))]

        try:
            result = await self._producer.send_and_wait(
                topic,
                value=event.to_json().encode("utf-8"),
                key=key.encode("utf-8") if key else None,
                headers=headers,
            )
            logger.info(
                f"Event sent successfully: topic={topic}, "
                f"event_id={event.event_id}, "
                f"partition={result.partition}, "
                f"offset={result.offset}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send event to {topic}: {e}")
            raise

    async def send_batch(
        self,
        topic: str,
        events: List[BaseEvent],
        key_func: Optional[callable] = None,
    ) -> int:
        if not self._started:
            await self.start()

        sent_count = 0
        for event in events:
            key = key_func(event) if key_func else None
            try:
                await self.send(topic, event, key)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send batch event: {e}")

        return sent_count


class EventBus:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = KafkaProducerClient(bootstrap_servers)
        self._topics: Dict[str, str] = {
            "user": "baixing.user.events",
            "payment": "baixing.payment.events",
            "legal": "baixing.legal.events",
            "news": "baixing.news.events",
            "chat": "baixing.chat.events",
            "order": "baixing.order.events",
            "notification": "baixing.notification.events",
        }
        self._started = False

    async def start(self):
        if not self._started:
            await self.producer.start()
            self._started = True

    async def stop(self):
        if self._started:
            await self.producer.stop()
            self._started = False

    async def publish_user_event(self, event: BaseEvent, user_id: str) -> bool:
        return await self.producer.send(
            self._topics["user"], event, key=user_id
        )

    async def publish_payment_event(self, event: BaseEvent, payment_id: str) -> bool:
        return await self.producer.send(
            self._topics["payment"], event, key=payment_id
        )

    async def publish_legal_event(self, event: BaseEvent, lawyer_id: str) -> bool:
        return await self.producer.send(
            self._topics["legal"], event, key=lawyer_id
        )

    async def publish_news_event(self, event: BaseEvent, news_id: str) -> bool:
        return await self.producer.send(
            self._topics["news"], event, key=news_id
        )

    async def publish_chat_event(self, event: BaseEvent, session_id: str) -> bool:
        return await self.producer.send(
            self._topics["chat"], event, key=session_id
        )

    async def publish_order_event(self, event: BaseEvent, order_id: str) -> bool:
        return await self.producer.send(
            self._topics["order"], event, key=order_id
        )

    async def publish_notification_event(
        self, event: BaseEvent, notification_id: str
    ) -> bool:
        return await self.producer.send(
            self._topics["notification"], event, key=notification_id
        )

    def get_topic(self, name: str) -> str:
        return self._topics.get(name, name)


_event_bus: Optional[EventBus] = None


def get_event_bus(bootstrap_servers: Optional[str] = None) -> EventBus:
    global _event_bus
    if _event_bus is None:
        bootstrap_servers = bootstrap_servers or "localhost:9092"
        _event_bus = EventBus(bootstrap_servers)
    return _event_bus


async def init_event_bus(bootstrap_servers: Optional[str] = None):
    bus = get_event_bus(bootstrap_servers)
    await bus.start()
    return bus


async def close_event_bus():
    global _event_bus
    if _event_bus:
        await _event_bus.stop()
        _event_bus = None
