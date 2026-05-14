"""AI Service Kafka 事件定义"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, Any, Dict
import json
import uuid


@dataclass
class AIEvent:
    event_id: str
    event_type: str
    timestamp: str
    version: str
    source: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "AIEvent":
        return cls(**json.loads(data))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AIEventTypes:
    CHAT_STARTED = "ai.chat.started"
    CHAT_COMPLETED = "ai.chat.completed"
    CHAT_FAILED = "ai.chat.failed"
    RAG_QUERY = "ai.rag.query"
    RAG_RESULT = "ai.rag.result"
    AGENT_EXECUTED = "ai.agent.executed"
    DOCUMENT_INDEXED = "ai.document.indexed"
    DOCUMENT_INDEX_FAILED = "ai.document.index_failed"


class AIEventBus:
    def __init__(self, producer_client):
        self._producer = producer_client

    async def publish_ai_event(self, event: AIEvent, key: Optional[str] = None):
        await self._producer.send(
            topic="baixing.ai.events",
            value=event.to_json(),
            key=key,
        )

    async def publish_conversation_event(
        self,
        event: AIEvent,
        conversation_id: str,
    ):
        await self.publish_ai_event(event, key=conversation_id)

    async def publish_user_event(
        self,
        event: AIEvent,
        user_id: str,
    ):
        await self.publish_ai_event(event, key=user_id)


def create_ai_event(
    event_type: str,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    source: str = "ai-service",
) -> AIEvent:
    return AIEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0",
        source=source,
        conversation_id=conversation_id,
        user_id=user_id,
        payload=payload or {},
    )
