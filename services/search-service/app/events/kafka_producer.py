"""Search Service Kafka 事件发布"""

import logging
from typing import Optional

from .search_events import (
    SearchEventBus,
    SearchEvent,
    SearchEventTypes,
    create_search_event,
)
from services.common.events import (
    EventBus,
    init_event_bus,
    close_event_bus,
)

logger = logging.getLogger(__name__)

_event_bus: Optional[SearchEventBus] = None


async def init_kafka_producer(bootstrap_servers: str = "kafka:9092"):
    """初始化 Kafka 生产者"""
    global _event_bus
    event_bus = await init_event_bus(bootstrap_servers)
    _event_bus = SearchEventBus(event_bus._producer)
    logger.info(f"Search service Kafka producer initialized: {bootstrap_servers}")
    return _event_bus


async def close_kafka_producer():
    """关闭 Kafka 生产者"""
    global _event_bus
    if _event_bus:
        await close_event_bus()
        _event_bus = None
        logger.info("Search service Kafka producer closed")


async def publish_search_query(
    user_id: str,
    query: str,
    filters: Optional[dict] = None,
) -> bool:
    """发布搜索查询事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_search_event(
        event_type=SearchEventTypes.SEARCH_QUERY,
        query=query,
        user_id=user_id,
        payload={"filters": filters} if filters else {},
        source="search-service",
    )

    try:
        await _event_bus.publish_query_event(event, user_id)
        logger.info(f"Published search.query event for user: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish search.query event: {e}")
        return False


async def publish_search_result(
    user_id: str,
    query: str,
    results_count: int,
    top_results: Optional[list] = None,
) -> bool:
    """发布搜索结果事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_search_event(
        event_type=SearchEventTypes.SEARCH_RESULT,
        query=query,
        user_id=user_id,
        results_count=results_count,
        payload={"top_results": top_results[:5] if top_results else []},
        source="search-service",
    )

    try:
        await _event_bus.publish_query_event(event, user_id)
        logger.info(f"Published search.result event: {results_count} results")
        return True
    except Exception as e:
        logger.error(f"Failed to publish search.result event: {e}")
        return False


async def publish_no_result(
    user_id: str,
    query: str,
    suggestion: Optional[str] = None,
) -> bool:
    """发布无结果事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_search_event(
        event_type=SearchEventTypes.SEARCH_NO_RESULT,
        query=query,
        user_id=user_id,
        results_count=0,
        payload={"suggestion": suggestion} if suggestion else {},
        source="search-service",
    )

    try:
        await _event_bus.publish_query_event(event, user_id)
        logger.info(f"Published search.no_result event: {query}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish search.no_result event: {e}")
        return False
