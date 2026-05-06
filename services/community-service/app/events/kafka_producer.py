"""Community Service Kafka 事件发布"""

import logging
from typing import Optional

from .community_events import (
    CommunityEventBus,
    CommunityEvent,
    CommunityEventTypes,
    create_community_event,
)
from services.common.events import (
    init_event_bus,
    close_event_bus,
)

logger = logging.getLogger(__name__)

_event_bus: Optional[CommunityEventBus] = None


async def init_kafka_producer(bootstrap_servers: str = "kafka:9092"):
    """初始化 Kafka 生产者"""
    global _event_bus
    event_bus = await init_event_bus(bootstrap_servers)
    _event_bus = CommunityEventBus(event_bus._producer)
    logger.info(f"Community service Kafka producer initialized: {bootstrap_servers}")
    return _event_bus


async def close_kafka_producer():
    """关闭 Kafka 生产者"""
    global _event_bus
    if _event_bus:
        await close_event_bus()
        _event_bus = None
        logger.info("Community service Kafka producer closed")


async def publish_post_created(
    post_id: str,
    user_id: str,
    title: str,
) -> bool:
    """发布帖子创建事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_community_event(
        event_type=CommunityEventTypes.POST_CREATED,
        post_id=post_id,
        user_id=user_id,
        payload={"title": title},
        source="community-service",
    )

    try:
        await _event_bus.publish_post_event(event, post_id)
        logger.info(f"Published post.created event: {post_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish post.created event: {e}")
        return False


async def publish_comment_added(
    post_id: str,
    user_id: str,
    comment_id: str,
) -> bool:
    """发布评论添加事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_community_event(
        event_type=CommunityEventTypes.COMMENT_ADDED,
        post_id=post_id,
        user_id=user_id,
        payload={"comment_id": comment_id},
        source="community-service",
    )

    try:
        await _event_bus.publish_post_event(event, post_id)
        logger.info(f"Published comment.added event: {comment_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish comment.added event: {e}")
        return False
