"""带链路追踪的 Kafka 生产者"""

import asyncio
import logging
from typing import Optional, Dict, List
from aiokafka import AIOKafkaProducer
from opentelemetry import trace

from .kafka_events import BaseEvent
from ..tracing import inject_trace_context, add_span_attributes

logger = logging.getLogger(__name__)

tracer = trace.get_tracer("kafka-producer")


class TracingKafkaProducer:
    def __init__(
        self,
        bootstrap_servers: str,
        client_id: str = "baixing-tracing-producer",
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
            logger.info(f"Tracing Kafka producer started: {self.bootstrap_servers}")

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None
            self._started = False
            logger.info("Tracing Kafka producer stopped")

    async def send(
        self,
        topic: str,
        event: BaseEvent,
        key: Optional[str] = None,
        headers: Optional[List[tuple]] = None,
    ) -> bool:
        if not self._started:
            await self.start()

        current_span = trace.get_current_span()
        span_context = None
        if current_span and current_span.is_recording():
            span_context = current_span.get_span_context()
            add_span_attributes({
                "messaging.system": "kafka",
                "messaging.destination": topic,
                "messaging.destination_kind": "topic",
                "event.id": event.event_id,
                "event.type": event.event_type,
            })

        if headers is None:
            headers = [("event_type", event.event_type.encode("utf-8"))]
        else:
            headers = list(headers) + [("event_type", event.event_type.encode("utf-8"))]

        carrier: Dict[str, str] = {}
        inject_trace_context(carrier)
        for k, v in carrier.items():
            headers.append((k, v.encode("utf-8")))

        try:
            result = await self._producer.send_and_wait(
                topic,
                value=event.to_json().encode("utf-8"),
                key=key.encode("utf-8") if key else None,
                headers=headers,
            )

            if span_context and span_context.is_valid:
                add_span_attributes({
                    "messaging.kafka.partition": result.partition,
                    "messaging.kafka.offset": result.offset,
                })

            logger.info(
                f"Tracing event sent: topic={topic}, "
                f"event_id={event.event_id}, "
                f"partition={result.partition}, "
                f"offset={result.offset}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send tracing event to {topic}: {e}")
            raise


class TracingEventBus:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = TracingKafkaProducer(bootstrap_servers)
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
        with tracer.start_as_current_span(
            f"publish.{event.event_type}",
            kind=trace.SpanKind.PRODUCER,
        ) as span:
            span.set_attribute("messaging.destination", self._topics["user"])
            span.set_attribute("user.id", user_id)
            return await self.producer.send(self._topics["user"], event, key=user_id)

    async def publish_payment_event(self, event: BaseEvent, payment_id: str) -> bool:
        with tracer.start_as_current_span(
            f"publish.{event.event_type}",
            kind=trace.SpanKind.PRODUCER,
        ) as span:
            span.set_attribute("messaging.destination", self._topics["payment"])
            span.set_attribute("payment.id", payment_id)
            return await self.producer.send(self._topics["payment"], event, key=payment_id)

    def get_topic(self, name: str) -> str:
        return self._topics.get(name, name)


_tracing_event_bus: Optional[TracingEventBus] = None


def get_tracing_event_bus(bootstrap_servers: Optional[str] = None) -> TracingEventBus:
    global _tracing_event_bus
    if _tracing_event_bus is None:
        bootstrap_servers = bootstrap_servers or "localhost:9092"
        _tracing_event_bus = TracingEventBus(bootstrap_servers)
    return _tracing_event_bus


async def init_tracing_event_bus(bootstrap_servers: Optional[str] = None):
    bus = get_tracing_event_bus(bootstrap_servers)
    await bus.start()
    return bus


async def close_tracing_event_bus():
    global _tracing_event_bus
    if _tracing_event_bus:
        await _tracing_event_bus.stop()
        _tracing_event_bus = None
