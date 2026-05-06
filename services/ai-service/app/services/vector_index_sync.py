"""Kafka事件消费者 - 知识库/档案库变更监听"""
import asyncio
import json
import logging
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EventType(str, Enum):
    KNOWLEDGE_CREATED = "knowledge.created"
    KNOWLEDGE_UPDATED = "knowledge.updated"
    KNOWLEDGE_DELETED = "knowledge.deleted"
    ARCHIVE_CREATED = "archive.created"
    ARCHIVE_UPDATED = "archive.updated"
    ARCHIVE_DELETED = "archive.deleted"


@dataclass
class VectorIndexEvent:
    event_type: str
    doc_id: str
    content: str
    metadata: dict
    collection: str


class VectorIndexEventHandler:
    """向量索引事件处理器"""

    def __init__(self):
        self._handlers: dict[str, Callable] = {}

    def register(self, event_type: str, handler: Callable):
        self._handlers[event_type] = handler
        logger.info(f"Registered handler for event: {event_type}")

    async def handle(self, event: VectorIndexEvent):
        handler = self._handlers.get(event.event_type)
        if handler:
            try:
                await handler(event)
                logger.info(f"Handled event: {event.event_type}, doc_id: {event.doc_id}")
            except Exception as e:
                logger.error(f"Error handling event {event.event_type}: {e}")
        else:
            logger.warning(f"No handler for event type: {event.event_type}")

    def _create_knowledge_handler(self):
        """创建知识库事件处理器"""
        async def handle(event: VectorIndexEvent):
            if event.event_type == EventType.KNOWLEDGE_CREATED:
                await self._add_to_vector_store(event)
            elif event.event_type == EventType.KNOWLEDGE_UPDATED:
                await self._update_vector_store(event)
            elif event.event_type == EventType.KNOWLEDGE_DELETED:
                await self._delete_from_vector_store(event)

        return handle

    def _create_archive_handler(self):
        """创建档案库事件处理器"""
        async def handle(event: VectorIndexEvent):
            if event.event_type == EventType.ARCHIVE_CREATED:
                await self._add_to_vector_store(event)
            elif event.event_type == EventType.ARCHIVE_UPDATED:
                await self._update_vector_store(event)
            elif event.event_type == EventType.ARCHIVE_DELETED:
                await self._delete_from_vector_store(event)

        return handle

    async def _add_to_vector_store(self, event: VectorIndexEvent):
        """添加到向量库"""
        try:
            if event.collection == "knowledge":
                from app.services.knowledge_vector_store import add_knowledge
                add_knowledge(
                    documents=[{"content": event.content, "metadata": event.metadata}],
                    ids=[event.doc_id]
                )
            elif event.collection == "archive":
                from app.services.archive_vector_store import add_archive
                add_archive(
                    documents=[{"content": event.content, "metadata": event.metadata}],
                    ids=[event.doc_id]
                )
            logger.info(f"Added document {event.doc_id} to {event.collection}")
        except Exception as e:
            logger.error(f"Failed to add document to vector store: {e}")

    async def _update_vector_store(self, event: VectorIndexEvent):
        """更新向量库"""
        await self._delete_from_vector_store(event)
        await self._add_to_vector_store(event)

    async def _delete_from_vector_store(self, event: VectorIndexEvent):
        """从向量库删除"""
        try:
            if event.collection == "knowledge":
                from app.services.knowledge_vector_store import delete_knowledge
                delete_knowledge(ids=[event.doc_id])
            elif event.collection == "archive":
                from app.services.archive_vector_store import delete_archive
                delete_archive(ids=[event.doc_id])
            logger.info(f"Deleted document {event.doc_id} from {event.collection}")
        except Exception as e:
            logger.error(f"Failed to delete document from vector store: {e}")


class KafkaEventConsumer:
    """Kafka事件消费者"""

    def __init__(self, bootstrap_servers: str, group_id: str, topics: list[str]):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self._consumer = None
        self._handler = VectorIndexEventHandler()
        self._running = False
        self._setup_handlers()

    def _setup_handlers(self):
        """设置事件处理器"""
        self._handler.register(EventType.KNOWLEDGE_CREATED, self._handler._create_knowledge_handler())
        self._handler.register(EventType.KNOWLEDGE_UPDATED, self._handler._create_knowledge_handler())
        self._handler.register(EventType.KNOWLEDGE_DELETED, self._handler._create_knowledge_handler())
        self._handler.register(EventType.ARCHIVE_CREATED, self._handler._create_archive_handler())
        self._handler.register(EventType.ARCHIVE_UPDATED, self._handler._create_archive_handler())
        self._handler.register(EventType.ARCHIVE_DELETED, self._handler._create_archive_handler())

    async def start(self):
        """启动消费者"""
        try:
            from aiokafka import AIOKafkaConsumer

            self._consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True
            )

            await self._consumer.start()
            self._running = True
            logger.info(f"Kafka consumer started, topics: {self.topics}")

            await self._consume_loop()

        except ImportError:
            logger.warning("aiokafka not installed, using mock consumer")
            await self._mock_consume_loop()
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            await self._mock_consume_loop()

    async def _consume_loop(self):
        """消费循环"""
        try:
            async for message in self._consumer:
                if not self._running:
                    break

                try:
                    event_data = message.value
                    event = VectorIndexEvent(
                        event_type=event_data.get("event_type", ""),
                        doc_id=event_data.get("doc_id", ""),
                        content=event_data.get("content", ""),
                        metadata=event_data.get("metadata", {}),
                        collection=event_data.get("collection", "")
                    )
                    await self._handler.handle(event)

                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Consumer loop error: {e}")

    async def _mock_consume_loop(self):
        """模拟消费循环（用于测试）"""
        logger.info("Running mock consumer loop")
        while self._running:
            await asyncio.sleep(1)

    async def stop(self):
        """停止消费者"""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
            logger.info("Kafka consumer stopped")


class KafkaEventProducer:
    """Kafka事件生产者"""

    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self._producer = None

    async def start(self):
        """启动生产者"""
        try:
            from aiokafka import AIOKafkaProducer

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )

            await self._producer.start()
            logger.info("Kafka producer started")

        except ImportError:
            logger.warning("aiokafka not installed")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")

    async def send_event(self, topic: str, event: dict):
        """发送事件"""
        if self._producer:
            try:
                await self._producer.send_and_wait(topic, event)
                logger.info(f"Sent event to {topic}: {event.get('event_type')}")
            except Exception as e:
                logger.error(f"Failed to send event: {e}")

    async def stop(self):
        """停止生产者"""
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")


async def publish_knowledge_event(
    event_type: str,
    doc_id: str,
    content: str,
    metadata: dict
):
    """发布知识库变更事件"""
    kafka_url = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    producer = KafkaEventProducer(bootstrap_servers=kafka_url)
    await producer.start()

    try:
        await producer.send_event(
            topic="baixing.ai.events",
            event={
                "event_type": event_type,
                "doc_id": doc_id,
                "content": content,
                "metadata": metadata,
                "collection": "knowledge"
            }
        )
    finally:
        await producer.stop()


async def publish_archive_event(
    event_type: str,
    doc_id: str,
    content: str,
    metadata: dict
):
    """发布档案库变更事件"""
    kafka_url = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    producer = KafkaEventProducer(bootstrap_servers=kafka_url)
    await producer.start()

    try:
        await producer.send_event(
            topic="baixing.ai.events",
            event={
                "event_type": event_type,
                "doc_id": doc_id,
                "content": content,
                "metadata": metadata,
                "collection": "archive"
            }
        )
    finally:
        await producer.stop()


import os
_consumer: Optional[KafkaEventConsumer] = None


async def start_vector_index_sync():
    """启动向量索引同步消费者"""
    global _consumer

    kafka_url = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    group_id = os.getenv("KAFKA_GROUP_ID", "ai-service-vector-sync")

    _consumer = KafkaEventConsumer(
        bootstrap_servers=kafka_url,
        group_id=group_id,
        topics=["baixing.knowledge.events", "baixing.archive.events"]
    )

    await _consumer.start()
    return _consumer


async def stop_vector_index_sync():
    """停止向量索引同步"""
    global _consumer
    if _consumer:
        await _consumer.stop()
        _consumer = None
