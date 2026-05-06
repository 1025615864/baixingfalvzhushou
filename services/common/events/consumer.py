"""Kafka事件消费者"""
import json
import logging
from typing import Callable, Awaitable

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from ..config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

EventHandler = Callable[[dict], Awaitable[None]]


class KafkaConsumerManager:
    """Kafka消费者管理器"""

    def __init__(self):
        self._consumer: AIOKafkaConsumer | None = None
        self._handlers: dict[str, EventHandler] = {}
        self._running = False

    def register_handler(self, topic: str, event_type: str, handler: EventHandler):
        """注册事件处理器"""
        key = f"{topic}:{event_type}"
        self._handlers[key] = handler
        logger.info(f"Registered handler for {key}")

    async def start(self, topics: list[str], group_id: str = "user-service-consumer"):
        """启动消费者"""
        if not settings.kafka_enabled:
            logger.warning("Kafka is not enabled, skipping consumer start")
            return

        try:
            self._consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            await self._consumer.start()
            self._running = True
            logger.info(f"Kafka consumer started for topics: {topics}")

            asyncio.create_task(self._consume_loop())
        except KafkaError as e:
            logger.error(f"Failed to start Kafka consumer: {e}")

    async def _consume_loop(self):
        """消费循环"""
        if not self._consumer:
            return

        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    topic = message.topic
                    event_data = message.value
                    event_type = event_data.get("event_type", "unknown")

                    key = f"{topic}:{event_type}"
                    handler = self._handlers.get(key)

                    if handler:
                        await handler(event_data)
                    else:
                        logger.debug(f"No handler for {key}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except Exception as e:
            logger.error(f"Consumer loop error: {e}")

    async def stop(self):
        """停止消费者"""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None
            logger.info("Kafka consumer stopped")


import asyncio
consumer_manager = KafkaConsumerManager()
