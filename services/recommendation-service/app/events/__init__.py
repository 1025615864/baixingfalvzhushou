"""Recommendation Service 事件模块"""

from .kafka_producer import (
    init_kafka_producer,
    close_kafka_producer,
    publish_recommendation_clicked,
)
from .recommendation_events import (
    RecommendationEvent,
    RecommendationEventTypes,
    RecommendationEventBus,
    create_recommendation_event,
)

__all__ = [
    "init_kafka_producer",
    "close_kafka_producer",
    "publish_recommendation_clicked",
    "RecommendationEvent",
    "RecommendationEventTypes",
    "RecommendationEventBus",
    "create_recommendation_event",
]
