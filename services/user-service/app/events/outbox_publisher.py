"""Outbox Publisher - 确保事件可靠发布

工作机制：
1. 事件先写入 Outbox 表（与业务在同一事务）
2. 后台任务扫描 Outbox 发送到 Kafka
3. 发送成功后标记为 published
4. 失败重试最多 5 次
"""
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models.outbox import OutboxEvent, OutboxStatus
from .kafka_producer import _event_bus
from services.common.events.kafka_events import UserEvent

logger = logging.getLogger(__name__)

MAX_RETRY_COUNT = 5
BATCH_SIZE = 100
FLUSH_INTERVAL_SECONDS = 5


class OutboxPublisher:
    """Outbox 事件发布器"""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """启动 Outbox 刷新任务"""
        if self._running:
            logger.warning("Outbox publisher already running")
            return

        self._running = True
        self._shutdown_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Outbox publisher started")

    async def stop(self):
        """停止 Outbox 刷新任务"""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Outbox publisher shutdown timeout, cancelling task")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        logger.info("Outbox publisher stopped")

    async def _run_loop(self):
        """运行刷新循环"""
        while not self._shutdown_event.is_set():
            try:
                await self._flush_outbox()
            except Exception as e:
                logger.error(f"Outbox flush error: {e}")

            await asyncio.wait_for(
                self._shutdown_event.wait(),
                timeout=FLUSH_INTERVAL_SECONDS
            )

    async def _flush_outbox(self):
        """扫描并发送待发布事件"""
        async with AsyncSessionLocal() as session:
            events = await self._fetch_pending_events(session)

            if not events:
                return

            logger.debug(f"Found {len(events)} pending outbox events")

            for event in events:
                await self._publish_event(session, event)

            await session.commit()

    async def _fetch_pending_events(self, session: AsyncSession) -> List[OutboxEvent]:
        """获取待发布事件"""
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PENDING)
            .where(OutboxEvent.retry_count < MAX_RETRY_COUNT)
            .order_by(OutboxEvent.created_at)
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _publish_event(self, session: AsyncSession, event: OutboxEvent):
        """发布单个事件"""
        try:
            if _event_bus:
                user_event = UserEvent(
                    event_type=event.event_type,
                    user_id=event.payload.get("user_id", ""),
                    payload=event.payload,
                    source="user-service",
                )
                await _event_bus.publish_user_event(user_event, user_id=event.payload.get("user_id", ""))
                event.status = OutboxStatus.PUBLISHED
                event.published_at = datetime.utcnow()
                logger.info(f"Outbox event published: {event.event_type}")
            else:
                raise Exception("Kafka producer not initialized")

        except Exception as e:
            event.retry_count += 1
            event.error_message = str(e)[:500]

            if event.retry_count >= MAX_RETRY_COUNT:
                event.status = OutboxStatus.FAILED
                logger.error(
                    f"Outbox event failed after {MAX_RETRY_COUNT} retries: "
                    f"{event.event_type}, error: {e}"
                )
            else:
                logger.warning(
                    f"Outbox event retry {event.retry_count}: "
                    f"{event.event_type}, error: {e}"
                )

    async def publish_to_outbox(
        self,
        session: AsyncSession,
        event_type: str,
        topic: str,
        payload: dict,
    ) -> OutboxEvent:
        """将事件写入 Outbox 表（应在事务中调用）"""
        event = OutboxEvent(
            id=str(uuid4()),
            event_type=event_type,
            topic=topic,
            payload=payload,
            status=OutboxStatus.PENDING,
            retry_count=0,
        )
        session.add(event)
        logger.debug(f"Event added to outbox: {event_type}")
        return event


outbox_publisher = OutboxPublisher()
