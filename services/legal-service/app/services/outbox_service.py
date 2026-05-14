"""Outbox Publisher - 确保 Kafka 事件不丢失"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.outbox import OutboxEvent

logger = logging.getLogger(__name__)


class OutboxPublisher:
    """Outbox Publisher - 定期扫描 outbox 表发送到 Kafka

    使用 Outbox 模式确保事件可靠性：
    1. 业务操作和事件写入在同一事务中
    2. 后台任务定期扫描 pending 事件发送到 Kafka
    3. 发送成功后将状态改为 published
    4. 失败重试直到 max_retries 后标记为 failed
    """

    def __init__(
        self,
        session_factory,
        kafka_producer,
        batch_size: int = 100,
        retry_interval: float = 5.0,
    ):
        self._session_factory = session_factory
        self._kafka_producer = kafka_producer
        self._batch_size = batch_size
        self._retry_interval = retry_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """启动 Outbox Publisher"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._publish_loop())
        logger.info("Outbox publisher started")

    async def stop(self):
        """停止 Outbox Publisher"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Outbox publisher stopped")

    async def _publish_loop(self):
        """定期发布事件的循环"""
        while self._running:
            try:
                await self.publish_pending_events()
            except Exception as e:
                logger.error(f"Outbox publish loop error: {e}")
            await asyncio.sleep(self._retry_interval)

    async def publish_pending_events(self):
        """发布待处理的事件"""
        async with self._session_factory() as session:
            stmt = (
                select(OutboxEvent)
                .where(OutboxEvent.status == "pending")
                .where(OutboxEvent.retry_count < OutboxEvent.max_retries)
                .order_by(OutboxEvent.created_at)
                .limit(self._batch_size)
            )
            result = await session.execute(stmt)
            events = result.scalars().all()

            if not events:
                return

            for event in events:
                try:
                    await self._publish_event(session, event)
                except Exception as e:
                    logger.error(f"Failed to publish event {event.id}: {e}")
                    await self._mark_failed(session, event, str(e))

            await session.commit()

    async def _publish_event(self, session: AsyncSession, event: OutboxEvent):
        """发布单个事件到 Kafka"""
        await self._kafka_producer.send(
            topic=event.topic,
            value=event.payload,
            key=event.id,
        )
        event.status = "published"
        event.published_at = datetime.now(timezone.utc)
        logger.info(f"Outbox event published: {event.id} -> {event.topic}")

    async def _mark_failed(
        self,
        session: AsyncSession,
        event: OutboxEvent,
        error: str,
    ):
        """标记事件为失败"""
        event.retry_count += 1
        event.error_message = error
        if event.retry_count >= event.max_retries:
            event.status = "failed"
            logger.warning(f"Outbox event failed after {event.max_retries} retries: {event.id}")

    async def add_event(
        self,
        event_type: str,
        topic: str,
        payload: dict,
        session: AsyncSession,
    ) -> OutboxEvent:
        """添加新事件到 outbox 表（应在事务中使用）"""
        event = OutboxEvent(
            event_type=event_type,
            topic=topic,
            payload=payload,
            status="pending",
        )
        session.add(event)
        return event

    async def get_failed_events(
        self,
        limit: int = 100,
    ) -> list[OutboxEvent]:
        """获取失败的事件用于人工处理"""
        async with self._session_factory() as session:
            stmt = (
                select(OutboxEvent)
                .where(OutboxEvent.status == "failed")
                .order_by(OutboxEvent.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def retry_failed_event(self, event_id: str) -> bool:
        """重试失败的事件"""
        async with self._session_factory() as session:
            stmt = (
                update(OutboxEvent)
                .where(OutboxEvent.id == event_id)
                .where(OutboxEvent.status == "failed")
                .values(
                    status="pending",
                    retry_count=0,
                    error_message=None,
                )
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
