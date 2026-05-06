"""Recommendation Service Kafka 事件定义"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any, Dict
import json
import uuid


@dataclass
class RecommendationEvent:
    event_id: str
    event_type: str
    timestamp: str
    version: str
    source: str
    user_id: Optional[str] = None
    item_id: Optional[str] = None
    recommendation_type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "RecommendationEvent":
        return cls(**json.loads(data))


class RecommendationEventTypes:
    RECOMMENDATION_REQUESTED = "recommendation.requested"
    RECOMMENDATION_GENERATED = "recommendation.generated"
    RECOMMENDATION_CLICKED = "recommendation.clicked"
    RECOMMENDATION_CONVERTED = "recommendation.converted"


class RecommendationEventBus:
    def __init__(self, producer_client):
        self._producer = producer_client

    async def publish_recommendation_event(self, event: RecommendationEvent, key: Optional[str] = None):
        await self._producer.send(
            topic="baixing.recommendation.events",
            value=event.to_json(),
            key=key,
        )

    async def publish_user_event(self, event: RecommendationEvent, user_id: str):
        await self.publish_recommendation_event(event, key=user_id)


def create_recommendation_event(
    event_type: str,
    user_id: Optional[str] = None,
    item_id: Optional[str] = None,
    recommendation_type: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    source: str = "recommendation-service",
) -> RecommendationEvent:
    return RecommendationEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.utcnow().isoformat(),
        version="1.0",
        source=source,
        user_id=user_id,
        item_id=item_id,
        recommendation_type=recommendation_type,
        payload=payload or {},
    )
