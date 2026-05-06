"""News Service Kafka 事件发布"""

import logging
from typing import Optional

from .news_events import (
    NewsEventBus,
    NewsEvent,
    NewsEventTypes,
    create_news_event,
)
from services.common.events import (
    EventBus,
    init_event_bus,
    close_event_bus,
)

logger = logging.getLogger(__name__)

_event_bus: Optional[NewsEventBus] = None


async def init_kafka_producer(bootstrap_servers: str = "kafka:9092"):
    """初始化 Kafka 生产者"""
    global _event_bus
    event_bus = await init_event_bus(bootstrap_servers)
    _event_bus = NewsEventBus(event_bus._producer)
    logger.info(f"News service Kafka producer initialized: {bootstrap_servers}")
    return _event_bus


async def close_kafka_producer():
    """关闭 Kafka 生产者"""
    global _event_bus
    if _event_bus:
        await close_event_bus()
        _event_bus = None
        logger.info("News service Kafka producer closed")


async def publish_news_published(
    news_id: str,
    title: str,
    author_id: str,
    category: str,
) -> bool:
    """发布新闻发布事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_news_event(
        event_type=NewsEventTypes.NEWS_PUBLISHED,
        news_id=news_id,
        user_id=author_id,
        payload={
            "title": title,
            "category": category,
        },
        source="news-service",
    )

    try:
        await _event_bus.publish_news_event_with_id(event, news_id)
        logger.info(f"Published news.published event: {news_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish news.published event: {e}")
        return False


async def publish_comment_added(
    news_id: str,
    comment_id: str,
    user_id: str,
    content: str,
) -> bool:
    """发布评论添加事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_news_event(
        event_type=NewsEventTypes.COMMENT_ADDED,
        news_id=news_id,
        user_id=user_id,
        payload={
            "comment_id": comment_id,
            "content_preview": content[:100],
        },
        source="news-service",
    )

    try:
        await _event_bus.publish_news_event_with_id(event, news_id)
        logger.info(f"Published comment.added event: {comment_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish comment.added event: {e}")
        return False


async def publish_subscription_created(
    subscription_id: str,
    user_id: str,
    category: str,
) -> bool:
    """发布订阅创建事件"""
    if not _event_bus:
        logger.warning("Kafka producer not initialized")
        return False

    event = create_news_event(
        event_type=NewsEventTypes.SUBSCRIPTION_CREATED,
        user_id=user_id,
        payload={
            "subscription_id": subscription_id,
            "category": category,
        },
        source="news-service",
    )

    try:
        await _event_bus.publish_user_event(event, user_id)
        logger.info(f"Published subscription.created event: {subscription_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish subscription.created event: {e}")
        return False
