"""Kafka 事件发布/订阅客户端

提供事件驱动的消息队列接口。
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from .events.kafka_events import DomainEvent, Topic

logger = logging.getLogger(__name__)


@dataclass
class KafkaConfig:
    """Kafka 配置"""
    bootstrap_servers: str = "localhost:9092"
    client_id: str = "service-client"
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: str = "PLAIN"
    sasl_username: str = ""
    sasl_password: str = ""


class EventPublisher:
    """事件发布者

    发布领域事件到 Kafka。
    """

    def __init__(self, config: KafkaConfig):
        self.config = config
        self._producer = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """连接 Kafka"""
        try:
            from aiokafka import AIOKafkaProducer

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.config.bootstrap_servers,
                client_id=self.config.client_id,
                value_serializer=lambda v: json.dumps(v, default=str).encode(),
                key_serializer=lambda k: k.encode() if k else None,
                acks="all",
                retries=3,
                max_in_flight_requests_per_connection=1,
            )
            await self._producer.start()
            logger.info("Kafka producer connected")
        except ImportError:
            logger.warning("aiokafka not installed, using mock producer")
            self._producer = None
        except Exception as e:
            logger.error(f"Failed to connect Kafka producer: {e}")
            self._producer = None

    async def close(self) -> None:
        """关闭连接"""
        if self._producer:
            await self._producer.stop()
            self._producer = None

    async def publish(
        self,
        event: DomainEvent,
        key: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> bool:
        """发布事件

        Args:
            event: 领域事件
            key: 消息键（用于分区）
            topic: 目标 Topic（默认根据事件类型自动确定）

        Returns:
            是否发布成功
        """
        if not self._producer:
            logger.warning(f"Producer not connected, event dropped: {event.event_type}")
            return False

        try:
            target_topic = topic or Topic.for_event(event.event_type)

            # 如果事件没有 ID，生成一个
            if not event.event_id:
                event.event_id = str(uuid.uuid4())

            # 序列化事件
            value = event.to_dict()

            # 发送消息
            await self._producer.send_and_wait(
                target_topic,
                value=value,
                key=key,
            )

            logger.info(f"Event published: {event.event_type} to {target_topic}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    async def publish_batch(self, events: list[DomainEvent]) -> int:
        """批量发布事件"""
        success_count = 0
        for event in events:
            if await self.publish(event):
                success_count += 1
        return success_count


class EventConsumer:
    """事件消费者

    订阅和处理领域事件。
    """

    def __init__(
        self,
        config: KafkaConfig,
        group_id: str,
        topics: list[str],
    ):
        self.config = config
        self.group_id = group_id
        self.topics = topics
        self._consumer = None
        self._running = False
        self._handlers: dict[str, list[Callable]] = {}

    async def connect(self) -> None:
        """连接 Kafka"""
        try:
            from aiokafka import AIOKafkaConsumer

            self._consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.config.bootstrap_servers,
                group_id=self.group_id,
                client_id=f"{self.config.client_id}-consumer",
                value_deserializer=lambda v: json.loads(v.decode()),
                auto_offset_reset="earliest",
                enable_auto_commit=False,
            )
            await self._consumer.start()
            logger.info(f"Kafka consumer connected: {self.topics}")
        except ImportError:
            logger.warning("aiokafka not installed")
            self._consumer = None
        except Exception as e:
            logger.error(f"Failed to connect Kafka consumer: {e}")
            self._consumer = None

    async def close(self) -> None:
        """关闭连接"""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], Any]) -> None:
        """订阅事件类型

        Args:
            event_type: 事件类型（如 "payment.completed"）
            handler: 处理函数
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Subscribed to event: {event_type}")

    async def start(self) -> None:
        """开始消费"""
        if not self._consumer:
            logger.warning("Consumer not connected")
            return

        self._running = True
        logger.info("Starting event consumer...")

        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    event_data = message.value
                    event_type = event_data.get("event_type", "")

                    logger.debug(f"Received event: {event_type}")

                    # 查找并调用处理器
                    handlers = self._handlers.get(event_type, [])
                    for handler in handlers:
                        try:
                            await handler(event_data)
                        except Exception as e:
                            logger.error(f"Handler error for {event_type}: {e}")

                    # 提交偏移量
                    await self._consumer.commit()

                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except asyncio.CancelledError:
            logger.info("Consumer cancelled")
        finally:
            await self.close()

    async def stop(self) -> None:
        """停止消费"""
        self._running = False


# 全局发布者实例（单例）
_publisher: Optional[EventPublisher] = None


async def get_publisher(config: Optional[KafkaConfig] = None) -> EventPublisher:
    """获取全局事件发布者"""
    global _publisher
    if _publisher is None and config:
        _publisher = EventPublisher(config)
        await _publisher.connect()
    return _publisher


async def close_publisher() -> None:
    """关闭全局事件发布者"""
    global _publisher
    if _publisher:
        await _publisher.close()
        _publisher = None
