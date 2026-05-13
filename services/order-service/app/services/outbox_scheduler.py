import asyncio
import logging
import os

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class OutboxScheduler:
    def __init__(self):
        self.database_url = os.getenv(
            "ORDER_DATABASE_URL",
            os.getenv("DATABASE_URL", ""),
        )
        self._engine = None
        self._session_factory = None
        self._running = False
        self._poll_interval = int(os.getenv("OUTBOX_POLL_INTERVAL", "5"))

    async def start(self):
        if not self.database_url:
            logger.warning("No database URL for outbox scheduler")
            return

        self._engine = create_async_engine(self.database_url, echo=False)
        self._session_factory = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False,
        )
        self._running = True
        asyncio.create_task(self._poll_loop())
        logger.info(f"Outbox scheduler started (interval={self._poll_interval}s)")

    async def stop(self):
        self._running = False
        if self._engine:
            await self._engine.dispose()

    async def _poll_loop(self):
        while self._running:
            try:
                await self._process_pending()
            except Exception as e:
                logger.error(f"Outbox poll error: {e}")
            await asyncio.sleep(self._poll_interval)

    async def _process_pending(self):
        if not self._session_factory:
            return

        async with self._session_factory() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                    SELECT id, event_type, aggregate_id, payload
                    FROM outbox_events
                    WHERE status = 'PENDING'
                    ORDER BY created_at ASC
                    LIMIT 100
                """)
            )
            events = result.fetchall()

            for event in events:
                event_id, event_type, aggregate_id, payload = event
                try:
                    await self._publish_event(event_type, aggregate_id, payload)
                    await session.execute(
                        text("UPDATE outbox_events SET status = 'PUBLISHED' WHERE id = :id"),
                        {"id": event_id},
                    )
                    await session.commit()
                    logger.info(f"Published outbox event {event_id}: {event_type}")
                except Exception as e:
                    logger.error(f"Failed to publish outbox event {event_id}: {e}")
                    await session.execute(
                        text("""
                            UPDATE outbox_events
                            SET status = 'FAILED', error_message = :error
                            WHERE id = :id
                        """),
                        {"id": event_id, "error": str(e)[:500]},
                    )
                    await session.commit()

    async def _publish_event(self, event_type: str, aggregate_id: str, payload):
        try:
            from app.events.kafka_producer import event_publisher
            if event_publisher:
                await event_publisher.publish(event_type, payload)
        except ImportError:
            logger.debug("Kafka producer not available, skipping event publish")


outbox_scheduler = OutboxScheduler()
