"""订阅服务 - 服务层"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NewsSubscription


class SubscriptionService:
    """新闻订阅服务"""

    async def subscribe(
        self,
        session: AsyncSession,
        user_id: int,
        category_id: int,
    ) -> NewsSubscription:
        existing = await self.get_subscription(session, user_id, category_id)
        if existing:
            if not existing.enabled:
                existing.enabled = True
                await session.flush()
            return existing

        subscription = NewsSubscription(
            user_id=user_id,
            category_id=category_id,
            enabled=True,
        )
        session.add(subscription)
        await session.flush()
        return subscription

    async def unsubscribe(
        self,
        session: AsyncSession,
        user_id: int,
        category_id: int,
    ) -> bool:
        subscription = await self.get_subscription(session, user_id, category_id)
        if not subscription:
            return False

        subscription.enabled = False
        await session.flush()
        return True

    async def get_subscription(
        self,
        session: AsyncSession,
        user_id: int,
        category_id: int,
    ) -> Optional[NewsSubscription]:
        query = select(NewsSubscription).where(
            NewsSubscription.user_id == user_id,
            NewsSubscription.category_id == category_id,
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_subscriptions(
        self,
        session: AsyncSession,
        user_id: int,
        enabled_only: bool = True,
    ) -> List[NewsSubscription]:
        """获取用户所有订阅"""
        query = select(NewsSubscription).where(
            NewsSubscription.user_id == user_id,
        )
        if enabled_only:
            query = query.where(NewsSubscription.enabled == True)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def update_subscription(
        self,
        session: AsyncSession,
        user_id: int,
        category_id: int,
        enabled: bool,
    ) -> Optional[NewsSubscription]:
        subscription = await self.get_subscription(session, user_id, category_id)
        if not subscription:
            return None

        subscription.enabled = enabled
        await session.flush()
        return subscription


subscription_service = SubscriptionService()
