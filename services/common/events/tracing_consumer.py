"""带链路追踪的 Kafka 消费者"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind, Status, StatusCode
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)


@dataclass
class TracingMessage:
    topic: str
    partition: int
    offset: int
    key: Optional[str]
    value: Dict[str, Any]
    headers: Dict[str, str]
    span_context: Optional[Any] = None

    @property
    def event_id(self) -> Optional[str]:
        return self.value.get("event_id")

    @property
    def event_type(self) -> Optional[str]:
        return self.value.get("event_type")


class TracingKafkaConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: list,
        auto_offset_reset: str = "earliest",
        enable_auto_commit: bool = True,
        max_poll_records: int = 100,
        retry_limit: int = 3,
        dead_letter_topic: Optional[str] = None,
        service_name: str = "kafka-consumer",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.auto_offset_reset = auto_offset_reset
        self.enable_auto_commit = enable_auto_commit
        self.max_poll_records = max_poll_records
        self.retry_limit = retry_limit
        self.dead_letter_topic = dead_letter_topic
        self.service_name = service_name

        self._consumer: Optional[AIOKafkaConsumer] = None
        self._producer: Optional[AIOKafkaProducer] = None
        self._running = False
        self._handlers: Dict[str, Callable] = {}
        self._processed_count = 0
        self._error_count = 0

        self.tracer = trace.get_tracer(service_name)

    async def start(self):
        self._consumer = AIOKafkaConsumer(
            *self.topics,
            group_id=self.group_id,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset=self.auto_offset_reset,
            enable_auto_commit=self.enable_auto_commit,
            max_poll_records=self.max_poll_records,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

        if self.dead_letter_topic:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
            )
            await self._producer.start()

        await self._consumer.start()
        self._running = True
        logger.info(
            f"Tracing Kafka consumer started: topics={self.topics}, "
            f"group_id={self.group_id}"
        )

    async def stop(self):
        self._running = False

        if self._consumer:
            await self._consumer.stop()
            self._consumer = None

        if self._producer:
            await self._producer.stop()
            self._producer = None

        logger.info("Tracing Kafka consumer stopped")

    def register_handler(self, event_type: str, handler: Callable):
        self._handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    async def run(self):
        if not self._consumer:
            await self.start()

        logger.info("Starting Tracing Kafka consumer loop...")

        try:
            async for raw_message in self._consumer:
                if not self._running:
                    break

                await self._process_message(raw_message)

        except asyncio.CancelledError:
            logger.info("Tracing Kafka consumer cancelled")
        finally:
            await self.stop()

    async def _process_message(self, raw_message):
        try:
            headers = {
                h[0]: h[1].decode("utf-8") if h[1] else ""
                for h in (raw_message.headers or [])
            }

            carrier = {}
            for key, value in headers.items():
                if key not in ["event_type"]:
                    carrier[key] = value

            ctx = extract(carrier)

            message = TracingMessage(
                topic=raw_message.topic,
                partition=raw_message.partition,
                offset=raw_message.offset,
                key=raw_message.key.decode("utf-8") if raw_message.key else None,
                value=raw_message.value,
                headers=headers,
            )

            event_type = message.event_type
            if not event_type:
                logger.warning(f"Message without event_type: {message.event_id}")
                return

            handler = self._handlers.get(event_type)
            if not handler:
                logger.warning(f"No handler for event type: {event_type}")
                return

            with self.tracer.start_as_current_span(
                f"consume.{event_type}",
                context=ctx,
                kind=SpanKind.CONSUMER,
            ) as span:
                span.set_attribute("messaging.system", "kafka")
                span.set_attribute("messaging.destination", message.topic)
                span.set_attribute("messaging.destination_kind", "topic")
                span.set_attribute("messaging.kafka.partition", message.partition)
                span.set_attribute("messaging.kafka.offset", message.offset)
                span.set_attribute("event.id", message.event_id or "")
                span.set_attribute("event.type", event_type)

                for attempt in range(self.retry_limit + 1):
                    try:
                        await handler(message)
                        self._processed_count += 1
                        span.set_attribute("processing.success", True)
                        logger.info(
                            f"Message processed: {message.event_id}, "
                            f"processed_count={self._processed_count}"
                        )
                        return

                    except Exception as e:
                        logger.warning(
                            f"Error processing message (attempt {attempt + 1}): {e}"
                        )
                        if attempt < self.retry_limit:
                            await asyncio.sleep(2**attempt * 0.1)
                        else:
                            span.set_attribute("processing.success", False)
                            span.set_attribute("processing.error", str(e))
                            self._error_count += 1
                            await self._send_to_dead_letter(message)

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=e)
            self._error_count += 1
            span = trace.get_current_span()
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))

    async def _send_to_dead_letter(self, message: TracingMessage):
        if not self._producer or not self.dead_letter_topic:
            return

        try:
            await self._producer.send_and_wait(
                self.dead_letter_topic,
                value=json.dumps(message.value).encode("utf-8"),
                key=message.key.encode("utf-8") if message.key else None,
            )
            logger.info(f"Message sent to dead letter queue: {message.event_id}")
        except KafkaError as e:
            logger.error(f"Failed to send to dead letter queue: {e}")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "processed_count": self._processed_count,
            "error_count": self._error_count,
            "running": self._running,
            "topics": self.topics,
            "group_id": self.group_id,
        }
