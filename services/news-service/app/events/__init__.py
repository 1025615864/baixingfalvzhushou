"""News Service 事件模块"""

from .kafka_producer import (
    init_kafka_producer,
    close_kafka_producer,
    publish_news_published,
    publish_comment_added,
    publish_subscription_created,
)
from .news_events import (
    NewsEvent,
    NewsEventTypes,
    NewsEventBus,
    create_news_event,
)

__all__ = [
    "init_kafka_producer",
    "close_kafka_producer",
    "publish_news_published",
    "publish_comment_added",
    "publish_subscription_created",
    "NewsEvent",
    "NewsEventTypes",
    "NewsEventBus",
    "create_news_event",
]
