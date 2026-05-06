"""AI Service Kafka 事件发布"""

import logging
from typing import Optional

from .ai_events import (
    AIEventBus,
    AIEvent,
    AIEventTypes,
    create_ai_event,
)
from services.common.events import (
    EventBus,
    init_event_bus,
    close_event_bus,
)

logger = logging.getLogger(__name__)

_event_bus: Optional[AIEventBus] = None


async def init_kafka_producer(bootstrap_servers: str = "kafka:9092"):
    """初始化 Kafka 生产者"""
    global _event_bus
    event_bus = await init_event_bus(bootstrap_servers)
    _event_bus = AIEventBus(event_bus._producer)
    logger.info(f"AI service Kafka producer initialized: {bootstrap_servers}")
    return _event_bus


async def close_kafka_producer():
    """关闭 Kafka 生产者"""
    global _event_bus
    if _event_bus:
        await close_event_bus()
        _event_bus = None
        logger.info("AI service Kafka producer closed")


async def publish_chat_started(
    conversation_id: str,
    user_id: str,
    model: str,
) -> bool:
    """发布聊天开始事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_ai_event(
        event_type=AIEventTypes.CHAT_STARTED,
        conversation_id=conversation_id,
        user_id=user_id,
        payload={"model": model},
        source="ai-service",
    )

    try:
        await _event_bus.publish_conversation_event(event, conversation_id)
        logger.info(f"Published chat.started event: {conversation_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish chat.started event: {e}")
        return False


async def publish_chat_completed(
    conversation_id: str,
    user_id: str,
    tokens_used: int,
    duration_ms: int,
) -> bool:
    """发布聊天完成事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_ai_event(
        event_type=AIEventTypes.CHAT_COMPLETED,
        conversation_id=conversation_id,
        user_id=user_id,
        payload={
            "tokens_used": tokens_used,
            "duration_ms": duration_ms,
        },
        source="ai-service",
    )

    try:
        await _event_bus.publish_conversation_event(event, conversation_id)
        logger.info(f"Published chat.completed event: {conversation_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish chat.completed event: {e}")
        return False


async def publish_chat_failed(
    conversation_id: str,
    user_id: str,
    error: str,
) -> bool:
    """发布聊天失败事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_ai_event(
        event_type=AIEventTypes.CHAT_FAILED,
        conversation_id=conversation_id,
        user_id=user_id,
        payload={"error": error},
        source="ai-service",
    )

    try:
        await _event_bus.publish_conversation_event(event, conversation_id)
        logger.info(f"Published chat.failed event: {conversation_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish chat.failed event: {e}")
        return False


async def publish_rag_query(
    conversation_id: str,
    query: str,
    top_k: int,
) -> bool:
    """发布RAG查询事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_ai_event(
        event_type=AIEventTypes.RAG_QUERY,
        conversation_id=conversation_id,
        payload={
            "query": query,
            "top_k": top_k,
        },
        source="ai-service",
    )

    try:
        await _event_bus.publish_conversation_event(event, conversation_id)
        logger.info(f"Published rag.query event: {conversation_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish rag.query event: {e}")
        return False


async def publish_document_indexed(
    document_id: str,
    chunks_count: int,
    index_name: str,
) -> bool:
    """发布文档索引完成事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_ai_event(
        event_type=AIEventTypes.DOCUMENT_INDEXED,
        payload={
            "document_id": document_id,
            "chunks_count": chunks_count,
            "index_name": index_name,
        },
        source="ai-service",
    )

    try:
        await _event_bus.publish_ai_event(event, key=document_id)
        logger.info(f"Published document.indexed event: {document_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish document.indexed event: {e}")
        return False
