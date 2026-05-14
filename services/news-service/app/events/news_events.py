"""News Service Kafka 事件定义"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, Any, Dict
import json
import uuid


@dataclass
class NewsEvent:
    event_id: str
    event_type: str
    timestamp: str
    version: str
    source: str
    news_id: Optional[str] = None
    user_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "NewsEvent":
        return cls(**json.loads(data))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NewsEventTypes:
    NEWS_PUBLISHED = "news.published"
    NEWS_UPDATED = "news.updated"
    NEWS_DELETED = "news.deleted"
    NEWS_SUBMITTED = "news.submitted"
    NEWS_REVIEWED = "news.reviewed"
    NEWS_APPROVED = "news.approved"
    NEWS_REJECTED = "news.rejected"
    COMMENT_ADDED = "news.comment.added"
    COMMENT_DELETED = "news.comment.deleted"
    SUBSCRIPTION_CREATED = "news.subscription.created"
    SUBSCRIPTION_CANCELLED = "news.subscription.cancelled"
    EDITOR_ASSIGNED = "news.editor.assigned"
    AUDIT_LOG_CREATED = "news.audit.created"


class NewsEventBus:
    def __init__(self, producer_client):
        self._producer = producer_client

    async def publish_news_event(self, event: NewsEvent, key: Optional[str] = None):
        await self._producer.send(
            topic="baixing.news.events",
            value=event.to_json(),
            key=key,
        )

    async def publish_news_event_with_id(
        self,
        event: NewsEvent,
        news_id: str,
    ):
        await self.publish_news_event(event, key=news_id)

    async def publish_user_event(
        self,
        event: NewsEvent,
        user_id: str,
    ):
        await self.publish_news_event(event, key=user_id)


def create_news_event(
    event_type: str,
    news_id: Optional[str] = None,
    user_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    source: str = "news-service",
) -> NewsEvent:
    return NewsEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0",
        source=source,
        news_id=news_id,
        user_id=user_id,
        payload=payload or {},
    )
