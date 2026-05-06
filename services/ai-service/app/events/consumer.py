"""Kafka Consumer - 消费用户服务事件（AI Service）

订阅用户事件以维护用户权限白名单。
"""
import os
import json
import logging
from typing import Optional, Dict, Any, Callable

try:
    from aiokafka import AIOKafkaConsumer
except ImportError:
    AIOKafkaConsumer = None

import asyncio

logger = logging.getLogger(__name__)


class AIEventConsumer:
    """AI Service 事件消费者"""

    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.group_id = os.getenv("KAFKA_CONSUMER_GROUP_ID", "ai-service-user-events")
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._enabled = os.getenv("ENABLE_KAFKA_CONSUMER", "false").lower() in {"1", "true", "yes"}
        self._running = False
        self._handlers: Dict[str, Callable] = {}
        self._reconnect_delay = 5
        self._graceful_shutdown = False

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
                topics = ["baixing.user.events"]
                await self._consumer.start()
                await self._consumer.subscribe(topics)
                logger.info(f"Subscribed to topics: {topics}")
            except Exception as e:
                logger.error(f"Failed to create consumer: {e}")
                self._consumer = None
        return self._consumer

    async def close(self):
        logger.info("Initiating AI service consumer graceful shutdown...")
        self._graceful_shutdown = True
        self._running = False

        if self._consumer:
            try:
                await asyncio.wait_for(self._consumer.stop(), timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout stopping consumer")
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")
            self._consumer = None
        logger.info("AI service consumer shutdown complete")

    async def start(self):
        if not self._enabled:
            logger.info("Kafka consumer disabled, skipping start")
            return

        self._running = True
        self._graceful_shutdown = False
        logger.info("AI service event consumer starting...")

        while self._running and not self._graceful_shutdown:
            try:
                consumer = await self._get_consumer()
                if not consumer:
                    logger.warning(f"No consumer available, retrying in {self._reconnect_delay}s...")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, 60)
                    continue

                self._reconnect_delay = 5
                logger.info("AI service event consumer started")

                async for msg in consumer:
                    if not self._running or self._graceful_shutdown:
                        break
                    await self._process_message(msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consumer error: {e}, reconnecting...")
                if self._consumer:
                    try:
                        await self._consumer.stop()
                    except Exception:
                        pass
                    self._consumer = None
                await asyncio.sleep(self._reconnect_delay)

        await self.close()

    async def _process_message(self, msg):
        if msg.value is None:
            return

        topic = msg.topic
        value = msg.value
        event_type = value.get("event_type", "")
        event_id = value.get("event_id", "")

        logger.debug(f"Received event: {event_type} from topic: {topic}")

        handler = self._handlers.get(event_type)
        if handler:
            try:
                await handler(value)
                logger.info(f"Successfully processed event: {event_type}")
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")


async def handle_user_registered(event: Dict[str, Any]):
    """处理用户注册事件 - 更新AI服务白名单"""
    logger.info(f"Received user.registered event: {event}")
    user_id = event.get("user_id")
    if not user_id:
        return

    try:
        from app.services.white_list import user_white_list
        await user_white_list.add_user(int(user_id))
        logger.info(f"Added user {user_id} to AI service whitelist")
    except Exception as e:
        logger.error(f"Failed to add user {user_id} to whitelist: {e}")


async def handle_user_deleted(event: Dict[str, Any]):
    """处理用户删除事件 - 从AI服务白名单移除"""
    logger.info(f"Received user.account.deleted event: {event}")
    user_id = event.get("user_id")
    if not user_id:
        return

    try:
        from app.services.white_list import user_white_list
        await user_white_list.remove_user(int(user_id))
        logger.info(f"Removed user {user_id} from AI service whitelist")
    except Exception as e:
        logger.error(f"Failed to remove user {user_id} from whitelist: {e}")


async def handle_role_changed(event: Dict[str, Any]):
    """处理角色变更事件 - 更新用户权限"""
    logger.info(f"Received user.role.changed event: {event}")
    user_id = event.get("user_id")
    new_role = event.get("new_role")

    if not user_id:
        return

    try:
        from app.services.white_list import user_white_list
        await user_white_list.update_user_role(int(user_id), new_role)
        logger.info(f"Updated user {user_id} role to {new_role} in AI service")
    except Exception as e:
        logger.error(f"Failed to update user {user_id} role: {e}")


user_event_consumer = AIEventConsumer()
user_event_consumer.register_handler("user.registered", handle_user_registered)
user_event_consumer.register_handler("user.account.deleted", handle_user_deleted)
user_event_consumer.register_handler("user.role.changed", handle_role_changed)
