"""社区事件 Kafka 生产者"""
import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from aiokafka import AIOKafkaProducer
except ImportError:
    AIOKafkaProducer = None

from .community_events import (
    CommunityEvent,
    CommunityEventTypes,
    create_community_event,
)


class OpsEventTypes:
    USER_WARNED = "community.ops.user.warned"
    USER_MUTED = "community.ops.user.muted"
    USER_BANNED = "community.ops.user.banned"
    USER_UNMUTED = "community.ops.user.unmuted"
    USER_UNBANNED = "community.ops.user.unbanned"
    CONFIG_UPDATED = "community.ops.config.updated"
    ANNOUNCEMENT_PUBLISHED = "community.ops.announcement"
    POST_PINNED = "community.ops.post.pinned"
    POST_UNPINNED = "community.ops.post.unpinned"
    POST_FEATURED = "community.ops.post.featured"
    POST_UNFEATURED = "community.ops.post.unfeatured"
    POST_RECOMMENDED = "community.ops.post.recommended"
    POST_UNRECOMMENDED = "community.ops.post.unrecommended"
from .point_events import (
    CommunityPointEventTypes,
    COMMUNITY_POINTS_CONFIG,
)

logger = logging.getLogger(__name__)


class CommunityEventBus:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic = "baixing.community.events"
        self._producer = None
        self._enabled = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}

    async def _get_producer(self):
        if self._producer is None and self._enabled and AIOKafkaProducer:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
        return self._producer

    async def close(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None

    async def publish(self, event: CommunityEvent, key: Optional[str] = None):
        if not self._enabled:
            logger.info(f"Kafka disabled, skipping event: {event.event_type}")
            return

        producer = await self._get_producer()
        if not producer:
            logger.warning("Kafka producer not available")
            return

        try:
            await producer.send_and_wait(
                self.topic,
                value=event.to_dict(),
                key=key.encode("utf-8") if key else None,
                headers=[("event_type", event.event_type.encode("utf-8"))],
            )
            logger.info(f"Published event: {event.event_type} with key: {key}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")

    async def publish_post_created(self, post):
        event = create_community_event(
            event_type=CommunityEventTypes.POST_CREATED,
            post_id=str(post.id),
            user_id=str(post.user_id),
            payload={
                "title": post.title,
                "category": post.category,
                "author_name": post.author_name,
                "is_lawyer": post.is_lawyer,
                "points_action": CommunityPointEventTypes.POST_CREATED,
                "points_value": COMMUNITY_POINTS_CONFIG.get(CommunityPointEventTypes.POST_CREATED, {}).get("points", 5),
            }
        )
        await self.publish(event, key=str(post.id))

    async def publish_post_updated(self, post):
        event = create_community_event(
            event_type=CommunityEventTypes.POST_UPDATED,
            post_id=str(post.id),
            user_id=str(post.user_id),
            payload={"title": post.title}
        )
        await self.publish(event, key=str(post.id))

    async def publish_post_deleted(self, post):
        event = create_community_event(
            event_type=CommunityEventTypes.POST_DELETED,
            post_id=str(post.id),
            user_id=str(post.user_id),
        )
        await self.publish(event, key=str(post.id))

    async def publish_post_liked(self, post, user_id: int):
        event = create_community_event(
            event_type=CommunityEventTypes.LIKE_ADDED,
            post_id=str(post.id),
            user_id=str(user_id),
            payload={
                "points_action": CommunityPointEventTypes.POST_LIKED,
                "points_value": COMMUNITY_POINTS_CONFIG.get(CommunityPointEventTypes.POST_LIKED, {}).get("points", 1),
            }
        )
        await self.publish(event, key=str(post.id))

    async def publish_post_favorited(self, post, user_id: int):
        event = create_community_event(
            event_type="community.post.favorited",
            post_id=str(post.id),
            user_id=str(user_id),
        )
        await self.publish(event, key=str(post.id))

    async def publish_comment_created(self, comment):
        event = create_community_event(
            event_type=CommunityEventTypes.COMMENT_ADDED,
            post_id=str(comment.post_id),
            user_id=str(comment.user_id),
            payload={
                "comment_id": comment.id,
                "parent_id": comment.parent_id,
                "reply_to_user_id": comment.reply_to_user_id,
                "is_lawyer": comment.is_lawyer,
                "points_action": CommunityPointEventTypes.COMMENT_CREATED,
                "points_value": COMMUNITY_POINTS_CONFIG.get(CommunityPointEventTypes.COMMENT_CREATED, {}).get("points", 2),
            }
        )
        await self.publish(event, key=str(comment.post_id))

    async def publish_comment_deleted(self, comment):
        event = create_community_event(
            event_type=CommunityEventTypes.COMMENT_DELETED,
            post_id=str(comment.post_id),
            user_id=str(comment.user_id),
            payload={"comment_id": comment.id}
        )
        await self.publish(event, key=str(comment.post_id))

    async def publish_best_answer_selected(self, post, comment, selected_by: int):
        event = create_community_event(
            event_type=CommunityPointEventTypes.BEST_ANSWER_SELECTED,
            post_id=str(post.id),
            user_id=str(comment.user_id),
            payload={
                "comment_id": comment.id,
                "selected_by": selected_by,
                "is_lawyer": comment.is_lawyer,
                "points_action": CommunityPointEventTypes.BEST_ANSWER_SELECTED,
                "points_value": COMMUNITY_POINTS_CONFIG.get(CommunityPointEventTypes.BEST_ANSWER_SELECTED, {}).get("points", 10),
            }
        )
        await self.publish(event, key=str(post.id))


class OpsEventBus:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic = "baixing.community.ops.events"
        self._producer = None
        self._enabled = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}

    async def _get_producer(self):
        if self._producer is None and self._enabled and AIOKafkaProducer:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._producer.start()
        return self._producer

    async def close(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None

    async def publish(self, event: CommunityEvent, key: Optional[str] = None):
        if not self._enabled:
            logger.info(f"Kafka disabled, skipping ops event: {event.event_type}")
            return

        producer = await self._get_producer()
        if not producer:
            logger.warning("Kafka producer not available")
            return

        try:
            await producer.send_and_wait(
                self.topic,
                value=event.to_dict(),
                key=key.encode("utf-8") if key else None,
                headers=[("event_type", event.event_type.encode("utf-8"))],
            )
            logger.info(f"Published ops event: {event.event_type} with key: {key}")
        except Exception as e:
            logger.error(f"Failed to publish ops event: {e}")

    async def publish_user_penalized(
        self,
        user_id: int,
        penalty_type: str,
        reason: str = None,
        operator_id: int = 0,
        duration_hours: int = None
    ):
        event_type = {
            "warn": OpsEventTypes.USER_WARNED,
            "mute": OpsEventTypes.USER_MUTED,
            "ban": OpsEventTypes.USER_BANNED,
        }.get(penalty_type, OpsEventTypes.USER_WARNED)

        event = create_community_event(
            event_type=event_type,
            user_id=str(user_id),
            payload={
                "penalty_type": penalty_type,
                "reason": reason,
                "operator_id": operator_id,
                "duration_hours": duration_hours,
            }
        )
        await self.publish(event, key=str(user_id))

    async def publish_user_unpenalized(
        self,
        user_id: int,
        penalty_type: str,
        operator_id: int = 0,
        reason: str = None
    ):
        event_type = {
            "mute": OpsEventTypes.USER_UNMUTED,
            "ban": OpsEventTypes.USER_UNBANNED,
        }.get(penalty_type, OpsEventTypes.USER_UNMUTED)

        event = create_community_event(
            event_type=event_type,
            user_id=str(user_id),
            payload={
                "penalty_type": penalty_type,
                "operator_id": operator_id,
                "reason": reason,
            }
        )
        await self.publish(event, key=str(user_id))

    async def publish_config_updated(
        self,
        config_key: str,
        old_value: str = None,
        new_value: str = None,
        operator_id: int = 0
    ):
        event = create_community_event(
            event_type=OpsEventTypes.CONFIG_UPDATED,
            payload={
                "config_key": config_key,
                "old_value": old_value,
                "new_value": new_value,
                "operator_id": operator_id,
            }
        )
        await self.publish(event, key=config_key)

    async def publish_announcement(
        self,
        announcement_id: int,
        title: str,
        content: str,
        scope: str = "global",
        operator_id: int = 0
    ):
        event = create_community_event(
            event_type=OpsEventTypes.ANNOUNCEMENT_PUBLISHED,
            payload={
                "announcement_id": announcement_id,
                "title": title,
                "content": content,
                "scope": scope,
                "operator_id": operator_id,
            }
        )
        await self.publish(event, key=str(announcement_id))

    async def publish_post_operation(
        self,
        post_id: int,
        operation: str,
        operator_id: int = 0,
        reason: str = None
    ):
        event_type_map = {
            "pin": OpsEventTypes.POST_PINNED,
            "unpin": OpsEventTypes.POST_UNPINNED,
            "feature": OpsEventTypes.POST_FEATURED,
            "unfeature": OpsEventTypes.POST_UNFEATURED,
            "recommend": OpsEventTypes.POST_RECOMMENDED,
            "unrecommend": OpsEventTypes.POST_UNRECOMMENDED,
        }
        event_type = event_type_map.get(operation, OpsEventTypes.POST_PINNED)

        event = create_community_event(
            event_type=event_type,
            post_id=str(post_id),
            payload={
                "operation": operation,
                "operator_id": operator_id,
                "reason": reason,
            }
        )
        await self.publish(event, key=str(post_id))


ops_event_bus = OpsEventBus()
event_bus = CommunityEventBus()
