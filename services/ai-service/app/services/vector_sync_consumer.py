"""Kafka Consumer - 向量同步事件消费"""
import asyncio
import logging
from typing import Optional
from aiokafka import AIOKafkaConsumer

from app.config.settings import get_settings
from app.services.vector_store import ChineseEmbeddingFunction

settings = get_settings()
logger = logging.getLogger(__name__)


class VectorSyncConsumer:
    """向量同步Consumer"""

    def __init__(self):
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False

    async def start(self):
        """启动Consumer"""
        if not settings.kafka_bootstrap_servers:
            logger.warning("Kafka not configured, skipping consumer start")
            return

        try:
            self.consumer = AIOKafkaConsumer(
                "knowledge.published",
                "knowledge.updated",
                "knowledge.deleted",
                "archive.published",
                "archive.updated",
                "archive.deleted",
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id="vector-sync-consumer",
                auto_offset_reset="earliest"
            )
            await self.consumer.start()
            self.running = True
            logger.info("Vector sync consumer started")
            await self._consume_loop()
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            self.running = False

    async def stop(self):
        """停止Consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Vector sync consumer stopped")

    async def _consume_loop(self):
        """消费循环"""
        while self.running:
            try:
                async for message in self.consumer:
                    if not self.running:
                        break
                    await self._process_message(message)
            except Exception as e:
                logger.error(f"Consume loop error: {e}")
                await asyncio.sleep(1)

    async def _process_message(self, message):
        """处理消息"""
        topic = message.topic
        event_type = topic.split(".")[-1]
        data = message.value.decode("utf-8")

        logger.info(f"Received event: {topic}, data: {data[:100]}...")

        try:
            if topic.startswith("knowledge"):
                await self._handle_knowledge_event(event_type, data)
            elif topic.startswith("archive"):
                await self._handle_archive_event(event_type, data)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _handle_knowledge_event(self, event_type: str, data: str):
        """处理知识事件"""
        from app.services.legal_agent import get_vector_store

        if event_type == "deleted":
            vector_id = self._extract_vector_id(data)
            if vector_id:
                store = get_vector_store()
                store.delete(vector_id)
                logger.info(f"Deleted vector: {vector_id}")
        else:
            entity_data = self._parse_event_data(data)
            if entity_data and event_type in ["published", "updated"]:
                store = get_vector_store()
                content = self._build_knowledge_content(entity_data)
                metadata = {
                    "entity_id": entity_data.get("id"),
                    "type": "knowledge",
                    "category": entity_data.get("category"),
                    "title": entity_data.get("title")
                }
                vector_id = store.add_texts(
                    texts=[content],
                    metadatas=[metadata]
                )
                logger.info(f"Added knowledge vector: {vector_id}")

    async def _handle_archive_event(self, event_type: str, data: str):
        """处理案例事件"""
        from app.services.legal_agent import get_archive_vector_store

        if event_type == "deleted":
            vector_id = self._extract_vector_id(data)
            if vector_id:
                store = get_archive_vector_store()
                store.delete(vector_id)
                logger.info(f"Deleted archive vector: {vector_id}")
        else:
            entity_data = self._parse_event_data(data)
            if entity_data and event_type in ["published", "updated"]:
                store = get_archive_vector_store()
                content = self._build_case_content(entity_data)
                metadata = {
                    "entity_id": entity_data.get("id"),
                    "type": "case",
                    "category": entity_data.get("category"),
                    "court": entity_data.get("court")
                }
                vector_id = store.add_texts(
                    texts=[content],
                    metadatas=[metadata]
                )
                logger.info(f"Added archive vector: {vector_id}")

    def _parse_event_data(self, data: str) -> dict:
        """解析事件数据"""
        import json
        try:
            return json.loads(data)
        except:
            return {}

    def _extract_vector_id(self, data: str) -> Optional[str]:
        """提取向量ID"""
        entity_data = self._parse_event_data(data)
        return entity_data.get("vector_id")

    def _build_knowledge_content(self, data: dict) -> str:
        """构建知识内容"""
        parts = [
            data.get("title", ""),
            data.get("content", ""),
            data.get("summary", ""),
            data.get("keywords", "")
        ]
        return " | ".join([p for p in parts if p])

    def _build_case_content(self, data: dict) -> str:
        """构建案例内容"""
        parts = [
            data.get("title", ""),
            data.get("facts", ""),
            data.get("judgment", ""),
            data.get("key_points", ""),
            data.get("keywords", "")
        ]
        return " | ".join([p for p in parts if p])


_consumer_instance: Optional[VectorSyncConsumer] = None


def get_vector_sync_consumer() -> VectorSyncConsumer:
    global _consumer_instance
    if _consumer_instance is None:
        _consumer_instance = VectorSyncConsumer()
    return _consumer_instance


async def start_vector_sync_consumer():
    """启动向量同步Consumer"""
    consumer = get_vector_sync_consumer()
    await consumer.start()
    return consumer


async def stop_vector_sync_consumer():
    """停止向量同步Consumer"""
    global _consumer_instance
    if _consumer_instance:
        await _consumer_instance.stop()
        _consumer_instance = None
