"""Kafka Consumer - 消费用户服务事件（法律服务完整版）"""
import os
import json
import logging
from typing import Optional, Dict, Any, Callable
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
        self.dlq_key = "kafka:dlq:legal-service"

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
            }
            await client.lpush(self.dlq_key, json.dumps(dlq_entry))
            logger.warning(f"Sent message to DLQ: {topic}:{partition}:{offset}")
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")


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

    async def is_event_processed(self, event_id: str) -> bool:
        if not event_id:
            return False
        try:
            client = await self._get_client()
            return await client.exists(f"event:id:{event_id}") > 0
        except Exception:
            logger.error("检查事件是否已处理失败")
            return False

    async def mark_event_processed(self, event_id: str):
        if not event_id:
            return
        try:
            client = await self._get_client()
            await client.setex(f"event:id:{event_id}", self.ttl, "1")
        except Exception:
            logger.exception("标记事件已处理失败")


class LegalEventConsumer:
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.group_id = os.getenv("KAFKA_CONSUMER_GROUP_ID", "legal-service-user-events")
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._enabled = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}
        self._running = False
        self._handlers: Dict[str, Callable] = {}
        self._idempotency_store = EventIdempotencyStore()
        self._dlq = DeadLetterQueue()
        self._reconnect_delay = 5
        self._graceful_shutdown = False
        self._current_message_processing = False
        self._message_event = asyncio.Event()

    def register_handler(self, event_type: str, handler: Callable):
        self._handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    async def _get_consumer(self) -> Optional[AIOKafkaConsumer]:
        if self._consumer is None and self._enabled and AIOKafkaConsumer:
            try:
                self._consumer = AIOKafkaConsumer(
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                )
                topics = [
                    "baixing.user.events",
                ]
                await self._consumer.start()
                await self._consumer.subscribe(topics)
                logger.info(f"Subscribed to topics: {topics}")
            except Exception as e:
                logger.error(f"Failed to create consumer: {e}")
                self._consumer = None
        return self._consumer

    async def close(self):
        logger.info("Initiating legal consumer graceful shutdown...")
        self._graceful_shutdown = True

        if self._current_message_processing:
            try:
                await asyncio.wait_for(self._message_event.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for message processing")

        self._running = False

        if self._consumer:
            try:
                await asyncio.wait_for(self._consumer.stop(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout stopping consumer")
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")
            self._consumer = None

        await self._idempotency_store.close()
        await self._dlq.close()
        logger.info("Legal consumer shutdown complete")

    async def start(self):
        if not self._enabled:
            logger.info("Kafka consumer disabled, skipping start")
            return

        self._running = True
        self._graceful_shutdown = False
        logger.info("Legal event consumer starting...")

        while self._running and not self._graceful_shutdown:
            try:
                consumer = await self._get_consumer()
                if not consumer:
                    logger.warning(f"No consumer available, retrying in {self._reconnect_delay}s...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, 60)
                    continue

                self._reconnect_delay = 5
                logger.info("Legal event consumer started")

                async for msg in consumer:
                    if not self._running or self._graceful_shutdown:
                        break

                    self._current_message_processing = True
                    self._message_event.clear()

                    try:
                        await self._process_message(msg)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                    finally:
                        self._current_message_processing = False
                        self._message_event.set()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consumer error: {e}, reconnecting...")
                if self._consumer:
                    try:
                        await self._consumer.stop()
                    except Exception:
                        logger.error("停止Kafka消费者失败")
                    self._consumer = None
                await asyncio.sleep(self._reconnect_delay)

        await self.close()

    async def _process_message(self, msg):
        if msg.value is None:
            return

        topic = msg.topic
        offset = msg.offset
        partition = msg.partition
        value = msg.value
        event_type = value.get("event_type", "")
        event_id = value.get("event_id", "")

        logger.info(f"Received event: {event_type} from topic: {topic}")

        if await self._idempotency_store.is_event_processed(event_id):
            logger.debug(f"Event {event_id} already processed, skipping")
            return

        handler = self._handlers.get(event_type)
        if handler:
            try:
                await handler(value)
                await self._idempotency_store.mark_event_processed(event_id)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")
                await self._dlq.send_to_dlq(topic, partition, offset, str(e), value)
        else:
            logger.debug(f"No handler registered for event type: {event_type}")


async def handle_user_profile_updated(event: Dict[str, Any]):
    """处理用户资料更新事件"""
    logger.info(f"Received user.profile.updated event: {event}")
    user_id = event.get("user_id")
    if not user_id:
        return


async def handle_user_lawyer_verified(event: Dict[str, Any]):
    """处理律师认证事件"""
    logger.info(f"Received user.lawyer.verified event: {event}")
    lawyer_id = event.get("lawyer_id")
    if not lawyer_id:
        return

    try:
        from app.database import AsyncSessionLocal
        from app.services.lawyer_service import LawyerService

        async with AsyncSessionLocal() as db:
            service = LawyerService(db)
            await service.verify(int(lawyer_id))
            logger.info(f"Lawyer {lawyer_id} verified via event")
    except Exception as e:
        logger.error(f"Failed to verify lawyer via event: {e}")


async def handle_user_lawyer_status_changed(event: Dict[str, Any]):
    """处理律师状态变更事件"""
    logger.info(f"Received user.lawyer.status_changed event: {event}")
    lawyer_id = event.get("lawyer_id")
    new_status = event.get("status")

    if not lawyer_id or not new_status:
        return

    try:
        from app.database import AsyncSessionLocal
        from app.models import Lawyer

        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(select(Lawyer).where(Lawyer.id == int(lawyer_id)))
            lawyer = result.scalar_one_or_none()
            if lawyer:
                lawyer.status = new_status
                await db.commit()
                logger.info(f"Lawyer {lawyer_id} status changed to {new_status}")
    except Exception as e:
        logger.error(f"Failed to update lawyer status via event: {e}")


user_event_consumer = LegalEventConsumer()
user_event_consumer.register_handler("user.profile.updated", handle_user_profile_updated)
user_event_consumer.register_handler("user.lawyer.verified", handle_user_lawyer_verified)
user_event_consumer.register_handler("user.lawyer.status_changed", handle_user_lawyer_status_changed)