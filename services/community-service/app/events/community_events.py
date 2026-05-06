"""Community Service Kafka 事件定义"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any, Dict
import json
import uuid


@dataclass
class CommunityEvent:
    event_id: str
    event_type: str
    timestamp: str
    version: str
    source: str
    post_id: Optional[str] = None
    user_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "CommunityEvent":
        return cls(**json.loads(data))


class CommunityEventTypes:
    POST_CREATED = "community.post.created"
    POST_UPDATED = "community.post.updated"
    POST_DELETED = "community.post.deleted"
    COMMENT_ADDED = "community.comment.added"
    COMMENT_DELETED = "community.comment.deleted"
    LIKE_ADDED = "community.like.added"
    LIKE_REMOVED = "community.like.removed"


class CommunityEventBus:
    def __init__(self, producer_client):
        self._producer = producer_client

    async def publish_community_event(self, event: CommunityEvent, key: Optional[str] = None):
        await self._producer.send(
            topic="baixing.community.events",
            value=event.to_json(),
            key=key,
        )

    async def publish_post_event(self, event: CommunityEvent, post_id: str):
        await self.publish_community_event(event, key=post_id)


def create_community_event(
    event_type: str,
    post_id: Optional[str] = None,
    user_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    source: str = "community-service",
) -> CommunityEvent:
    return CommunityEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0",
        source=source,
        post_id=post_id,
        user_id=user_id,
        payload=payload or {},
    )
