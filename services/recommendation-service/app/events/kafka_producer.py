"""Recommendation Service Kafka 事件发布"""

import logging
from typing import Optional

from .recommendation_events import (
    RecommendationEventBus,
    RecommendationEvent,
    RecommendationEventTypes,
    create_recommendation_event,
)
from services.common.events import (
    init_event_bus,
    close_event_bus,
)

logger = logging.getLogger(__name__)

_event_bus: Optional[RecommendationEventBus] = None


async def init_kafka_producer(bootstrap_servers: str = "kafka:9092"):
    """初始化 Kafka 生产者"""
    global _event_bus
    event_bus = await init_event_bus(bootstrap_servers)
    _event_bus = RecommendationEventBus(event_bus._producer)
    logger.info(f"Recommendation service Kafka producer initialized: {bootstrap_servers}")
    return _event_bus


async def close_kafka_producer():
    """关闭 Kafka 生产者"""
    global _event_bus
    if _event_bus:
        await close_event_bus()
        _event_bus = None
        logger.info("Recommendation service Kafka producer closed")


async def publish_recommendation_clicked(
    user_id: str,
    item_id: str,
    recommendation_type: str,
) -> bool:
    """发布推荐点击事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_recommendation_event(
        event_type=RecommendationEventTypes.RECOMMENDATION_CLICKED,
        user_id=user_id,
        item_id=item_id,
        recommendation_type=recommendation_type,
        source="recommendation-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id)
        logger.info(f"Published recommendation.clicked event: {item_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish recommendation.clicked event: {e}")
        return False
