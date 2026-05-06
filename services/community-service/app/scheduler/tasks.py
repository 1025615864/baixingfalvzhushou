"""定时任务调度器 - 热度重算"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except ImportError:
    AsyncIOScheduler = None

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class HotScoreScheduler:
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._enabled = True
        self._db_session_factory = None

    def set_db_session_factory(self, factory):
        self._db_session_factory = factory

    def start(self):
        if not self._enabled:
            logger.info("Scheduler disabled, skipping start")
            return

        if AsyncIOScheduler is None:
            logger.warning("APScheduler not installed, scheduler disabled")
            return

        self.scheduler = AsyncIOScheduler()

        self.scheduler.add_job(
            self.recalculate_hot_scores,
            IntervalTrigger(minutes=5),
            id="hot_score_recalculation",
            name="Hot Score Recalculation",
            replace_existing=True,
        )

        self.scheduler.add_job(
            self.cleanup_processed_events,
            IntervalTrigger(hours=1),
            id="cleanup_events",
            name="Cleanup Processed Events",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Hot score scheduler started")

    def stop(self):
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None
            logger.info("Hot score scheduler stopped")

    async def recalculate_hot_scores(self):
        if not self._db_session_factory:
            logger.error("No DB session factory configured")
            return

        from app.models.post import Post
        from app.utils.scoring import calculate_hot_score

        async with self._db_session_factory() as session:
            try:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                stmt = select(Post).where(
                    and_(
                        Post.status == "published",
                        Post.created_at >= cutoff_time
                    )
                )
                result = await session.execute(stmt)
                posts = result.scalars().all()

                updated_count = 0
                for post in posts:
                    old_score = post.hot_score
                    new_score = calculate_hot_score(
                        likes=post.like_count,
                        comments=post.comment_count,
                        views=post.view_count,
                        favorites=post.favorite_count,
                        is_lawyer_post=post.is_lawyer,
                        created_at=post.created_at
                    )
                    if abs(old_score - new_score) > 0.0001:
                        post.hot_score = new_score
                        updated_count += 1

                if updated_count > 0:
                    await session.commit()
                    logger.info(f"Recalculated hot scores for {updated_count} posts")
                else:
                    logger.debug("No hot score updates needed")

            except Exception as e:
                await session.rollback()
                logger.error(f"Error recalculating hot scores: {e}")

    async def cleanup_processed_events(self):
        try:
            import redis.asyncio as redis
            redis_url = "redis://localhost:6379"
            client = redis.from_url(redis_url)

            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            logger.info(f"Event cleanup task ran at {cutoff}")

            await client.close()
        except Exception as e:
            logger.error(f"Error in event cleanup: {e}")


hot_score_scheduler = HotScoreScheduler()
