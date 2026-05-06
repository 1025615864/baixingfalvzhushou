"""Kafka事件模块 - 统一事件定义"""
import json
from datetime import datetime
from typing import Optional, Any
from enum import Enum


class EventType(str, Enum):
    """事件类型枚举"""
    PUBLISHED = "published"
    UPDATED = "updated"
    DELETED = "deleted"


class EventTopic(str, Enum):
    """事件主题"""
    KNOWLEDGE = "knowledge"
    ARCHIVE = "archive"
    VECTOR = "vector"
    USER = "user"
    PAYMENT = "payment"
    ORDER = "order"
    NOTIFICATION = "notification"


class VectorSyncEvent:
    """向量同步事件"""

    def __init__(
        self,
        topic: EventTopic,
        event_type: EventType,
        entity_id: int,
        data: dict,
        timestamp: Optional[str] = None
    ):
        self.topic = topic
        self.event_type = event_type
        self.entity_id = entity_id
        self.data = data
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps({
            "topic": self.topic.value,
            "event_type": self.event_type.value,
            "entity_id": self.entity_id,
            "data": self.data,
            "timestamp": self.timestamp
        })

    @classmethod
    def from_json(cls, json_str: str) -> "VectorSyncEvent":
        obj = json.loads(json_str)
        return cls(
            topic=EventTopic(obj["topic"]),
            event_type=EventType(obj["event_type"]),
            entity_id=obj["entity_id"],
            data=obj["data"],
            timestamp=obj.get("timestamp")
        )

    def get_collection_name(self) -> str:
        if self.topic == EventTopic.KNOWLEDGE:
            return "knowledge_laws"
        elif self.topic == EventTopic.ARCHIVE:
            return "archive_cases"
        return "unknown"


def create_knowledge_event(event_type: EventType, knowledge_id: int, data: dict) -> VectorSyncEvent:
    return VectorSyncEvent(
        topic=EventTopic.KNOWLEDGE,
        event_type=event_type,
        entity_id=knowledge_id,
        data=data
    )


def create_archive_event(event_type: EventType, case_id: int, data: dict) -> VectorSyncEvent:
    return VectorSyncEvent(
        topic=EventTopic.ARCHIVE,
        event_type=event_type,
        entity_id=case_id,
        data=data
    )
