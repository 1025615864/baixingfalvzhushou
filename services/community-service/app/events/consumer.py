"""Kafka Consumer - 消费用户服务事件（健壮版）"""
import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from aiokafka import AIOKafkaConsumer
except ImportError:
    AIOKafkaConsumer = None

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

import asyncio

logger = logging.getLogger(__name__)


class DeadLetterQueue:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client: Optional[redis.Redis] = None
        self.dlq_key = "kafka:dlq:community-service"
        self.max_retries = 3

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def send_to_dlq(self, topic: str, partition: int, offset: int, error: str, message: Any):
        try:
            client = await self._get_client()
            dlq_entry = {
                "topic": topic,
                "partition": partition,
                "offset": offset,
                "error": error,
                "message": str(message)[:1000],
                "timestamp": datetime.now().isoformat(),
                "retry_count": 0
            }
            await client.lpush(self.dlq_key, json.dumps(dlq_entry))
            logger.warning(f"Sent message to DLQ: {topic}:{partition}:{offset}, error: {error}")
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")

    async def get_dlq_size(self) -> int:
        try:
            client = await self._get_client()
            return await client.llen(self.dlq_key)
        except Exception:
            logger.error("获取死信队列大小失败")
            return 0


class EventIdempotencyStore:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client: Optional[redis.Redis] = None
        self.ttl = 86400

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    def _generate_event_key(self, topic: str, partition: int, offset: int) -> str:
        return f"event:processed:{topic}:{partition}:{offset}"

    async def is_processed(self, topic: str, partition: int, offset: int) -> bool:
        try:
            client = await self._get_client()
            key = self._generate_event_key(topic, partition, offset)
            return await client.exists(key) > 0
        except Exception:
            logger.error("检查事件是否已处理失败")
            return False

    async def mark_processed(self, topic: str, partition: int, offset: int):
        try:
            client = await self._get_client()
            key = self._generate_event_key(topic, partition, offset)
            await client.setex(key, self.ttl, "1")
        except Exception:
            logger.exception("标记事件已处理失败")

    async def is_event_processed(self, event_id: str) -> bool:
        if not event_id:
            return False
        try:
            client = await self._get_client()
            key = f"event:id:{event_id}"
            return await client.exists(key) > 0
        except Exception:
            logger.error("检查事件ID是否已处理失败")
            return False

    async def mark_event_processed(self, event_id: str):
        if not event_id:
            return
        try:
            client = await self._get_client()
            key = f"event:id:{event_id}"
            await client.setex(key, self.ttl, "1")
        except Exception:
            logger.exception("标记事件ID已处理失败")


class UserEventConsumer:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.group_id = os.getenv("KAFKA_CONSUMER_GROUP_ID", "community-service-user-events")
        self._consumer = None
        self._enabled = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}
        self._running = False
        self._handlers: Dict[str, callable] = {}
        self._idempotency_store = EventIdempotencyStore()
        self._dlq = DeadLetterQueue()
        self._reconnect_delay = 5
        self._max_reconnect_delay = 60
        self._graceful_shutdown = False
        self._current_message_processing = False
        self._message_event = asyncio.Event()
        self._consumer_task = None

    def register_handler(self, event_type: str, handler: callable):
        self._handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    async def _get_consumer(self):
        if self._consumer is None and self._enabled and AIOKafkaConsumer:
            try:
                self._consumer = AIOKafkaConsumer(
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                    value_deserializer=self._safe_deserialize,
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                    retry_backoff_ms=1000,
                    max_poll_interval_ms=300000,
                )
                topics = [
                    "baixing.user.events",
                    "user.profile.updated",
                    "user.lawyer.verified",
                ]
                await self._consumer.start()
                await self._consumer.subscribe(topics)
                logger.info(f"Subscribed to topics: {topics}")
            except Exception as e:
                logger.error(f"Failed to create consumer: {e}")
                self._consumer = None
        return self._consumer

    def _safe_deserialize(self, value: bytes) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to deserialize message: {e}")
            return None

    async def close(self):
        logger.info("Initiating graceful shutdown...")
        self._graceful_shutdown = True

        if self._current_message_processing:
            logger.info("Waiting for current message processing to complete...")
            try:
                await asyncio.wait_for(self._message_event.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for message processing, forcing shutdown")

        self._running = False

        if self._consumer:
            try:
                await asyncio.wait_for(self._consumer.stop(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout stopping consumer, forcing shutdown")
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")
            self._consumer = None

        await self._idempotency_store.close()
        await self._dlq.close()
        logger.info("Consumer shutdown complete")

    async def start(self):
        if not self._enabled:
            logger.info("Kafka consumer disabled, skipping start")
            return

        self._running = True
        self._graceful_shutdown = False
        logger.info("User event consumer starting...")

        while self._running and not self._graceful_shutdown:
            try:
                consumer = await self._get_consumer()
                if not consumer:
                    logger.warning(f"No consumer available, retrying in {self._reconnect_delay}s...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
                    continue

                self._reconnect_delay = 5
                logger.info("User event consumer started, listening for messages...")

                async for msg in consumer:
                    if not self._running or self._graceful_shutdown:
                        break

                    self._current_message_processing = True
                    self._message_event.clear()

                    try:
                        await self._process_message(msg)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        await self._dlq.send_to_dlq(
                            topic=msg.topic,
                            partition=msg.partition,
                            offset=msg.offset,
                            error=str(e),
                            message=msg.value
                        )
                    finally:
                        self._current_message_processing = False
                        self._message_event.set()

            except asyncio.CancelledError:
                logger.info("Consumer task cancelled")
                break
            except Exception as e:
                logger.error(f"Consumer error: {e}, reconnecting in {self._reconnect_delay}s...")
                if self._consumer:
                    try:
                        await self._consumer.stop()
                    except Exception:
                        logger.error("停止Kafka消费者失败")
                    self._consumer = None
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

        await self.close()

    async def _process_message(self, msg):
        if msg.value is None:
            logger.warning(f"Skipping message with deserialization error: {msg.topic}:{msg.partition}:{msg.offset}")
            await self._dlq.send_to_dlq(
                topic=msg.topic,
                partition=msg.partition,
                offset=msg.offset,
                error="deserialization_failed",
                message=msg.value
            )
            return

        topic = msg.topic
        partition = msg.partition
        offset = msg.offset
        value = msg.value
        event_type = value.get("event_type", "") if isinstance(value, dict) else ""
        event_id = value.get("event_id", "") if isinstance(value, dict) else ""

        logger.info(f"Received event: {event_type} from topic: {topic}, offset: {offset}")

        if await self._idempotency_store.is_event_processed(event_id):
            logger.debug(f"Event {event_id} already processed, skipping")
            return

        if await self._idempotency_store.is_processed(topic, partition, offset):
            logger.debug(f"Message at {topic}:{partition}:{offset} already processed, skipping")
            return

        handler = self._handlers.get(event_type)
        if handler:
            try:
                await handler(value)
                await self._idempotency_store.mark_event_processed(event_id)
                await self._idempotency_store.mark_processed(topic, partition, offset)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")
                raise
        else:
            logger.debug(f"No handler registered for event type: {event_type}")

    def get_dlq_size(self) -> int:
        return asyncio.create_task(self._dlq.get_dlq_size())


async def handle_user_profile_updated(event: Dict[str, Any]):
    from app.models.post import Post
    from app.database import AsyncSessionLocal

    user_id = event.get("user_id")
    if not user_id:
        return

    payload = event.get("payload", {})
    author_name = payload.get("author_name")
    avatar = payload.get("avatar")

    if not author_name and not avatar:
        return

    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select
            stmt = select(Post).where(
                Post.user_id == int(user_id),
                Post.is_deleted == False
            )
            result = await session.execute(stmt)
            posts = result.scalars().all()

            update_count = 0
            for post in posts:
                if author_name:
                    post.author_name = author_name
                if avatar:
                    post.author_avatar = avatar
                update_count += 1

            if update_count > 0:
                await session.commit()
                logger.info(f"Updated {update_count} posts for user {user_id}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update user profile on posts: {e}")


async def handle_user_lawyer_verified(event: Dict[str, Any]):
    from app.models.post import Post
    from app.database import AsyncSessionLocal

    user_id = event.get("user_id")
    if not user_id:
        return

    payload = event.get("payload", {})
    is_lawyer = payload.get("is_lawyer", False)

    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select
            stmt = select(Post).where(
                Post.user_id == int(user_id),
                Post.is_deleted == False
            )
            result = await session.execute(stmt)
            posts = result.scalars().all()

            update_count = 0
            for post in posts:
                post.is_lawyer = is_lawyer
                update_count += 1

            if update_count > 0:
                await session.commit()
                logger.info(f"Updated is_lawyer={is_lawyer} for {update_count} posts of user {user_id}")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update lawyer status on posts: {e}")


user_event_consumer = UserEventConsumer()
user_event_consumer.register_handler("user.profile.updated", handle_user_profile_updated)
user_event_consumer.register_handler("user.lawyer.verified", handle_user_lawyer_verified)
