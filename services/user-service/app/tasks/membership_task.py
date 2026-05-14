"""会员过期定时任务

定期检查会员过期并自动降级
"""
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import OutboxEvent, OutboxStatus
from ..events.outbox_publisher import outbox_publisher

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 300
BATCH_SIZE = 100


class MembershipExpiryTask:
    """会员过期检查任务"""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """启动会员过期检查任务"""
        if self._running:
            logger.warning("Membership expiry task already running")
            return

        self._running = True
        self._shutdown_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Membership expiry task started")

    async def stop(self):
        """停止会员过期检查任务"""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Membership expiry task shutdown timeout")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        logger.info("Membership expiry task stopped")

    async def _run_loop(self):
        """运行检查循环"""
        while not self._shutdown_event.is_set():
            try:
                await self._check_expiry()
            except Exception as e:
                logger.error(f"Membership expiry check error: {e}")

            await asyncio.wait_for(
                self._shutdown_event.wait(),
                timeout=CHECK_INTERVAL_SECONDS
            )

    async def _check_expiry(self):
        """检查并处理过期会员"""
        async with AsyncSessionLocal() as session:
            now = datetime.now(timezone.utc)

            stmt = (
                select(self._get_user_model())
                .where(self._get_user_model().vip_expires_at.isnot(None))
                .where(self._get_user_model().vip_expires_at <= now)
                .where(self._get_user_model().membership_tier.in_(["vip", "svip"]))
                .with_for_update(skip_locked=True)
                .limit(BATCH_SIZE)
            )

            result = await session.execute(stmt)
            expired_users = list(result.scalars().all())

            if not expired_users:
                return

            logger.info(f"Found {len(expired_users)} expired memberships")

            for user in expired_users:
                old_tier = user.membership_tier
                user.membership_tier = "free"
                user.vip_expires_at = None

                event = OutboxEvent(
                    id=str(self._generate_uuid()),
                    event_type="user.membership.expired",
                    topic="baixing.user.events",
                    payload={
                        "user_id": str(user.uid),
                        "previous_tier": old_tier,
                        "expired_at": now.isoformat(),
                    },
                    status=OutboxStatus.PENDING,
                    retry_count=0,
                )
                session.add(event)

                logger.info(
                    f"Membership expired: user_id={user.uid}, "
                    f"old_tier={old_tier}"
                )

            await session.commit()

    def _get_user_model(self):
        """获取 User 模型（延迟导入避免循环依赖）"""
        from ..models import User
        return User

    @staticmethod
    def _generate_uuid():
        """生成 UUID"""
        import uuid
        return uuid.uuid4()


membership_expiry_task = MembershipExpiryTask()
