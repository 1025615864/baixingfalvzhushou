"""Search Service Kafka 事件定义"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any, Dict
import json
import uuid


@dataclass
class SearchEvent:
    event_id: str
    event_type: str
    timestamp: str
    version: str
    source: str
    query: Optional[str] = None
    user_id: Optional[str] = None
    results_count: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "SearchEvent":
        return cls(**json.loads(data))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SearchEventTypes:
    SEARCH_QUERY = "search.query"
    SEARCH_RESULT = "search.result"
    SEARCH_NO_RESULT = "search.no_result"
    INDEX_UPDATED = "search.index.updated"


class SearchEventBus:
    def __init__(self, producer_client):
        self._producer = producer_client

    async def publish_search_event(self, event: SearchEvent, key: Optional[str] = None):
        await self._producer.send(
            topic="baixing.search.events",
            value=event.to_json(),
            key=key,
        )

    async def publish_query_event(
        self,
        event: SearchEvent,
        user_id: str,
    ):
        await self.publish_search_event(event, key=user_id)


def create_search_event(
    event_type: str,
    query: Optional[str] = None,
    user_id: Optional[str] = None,
    results_count: Optional[int] = None,
    payload: Optional[Dict[str, Any]] = None,
    source: str = "search-service",
) -> SearchEvent:
    return SearchEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.utcnow().isoformat(),
        version="1.0",
        source=source,
        query=query,
        user_id=user_id,
        results_count=results_count,
        payload=payload or {},
    )
