"""新闻订阅和收藏服务

提供新闻订阅、收藏、热门推荐等功能
"""
import json
import logging
from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.news import News, NewsFavorite, NewsSubscription
from ...models.notification import Notification, NotificationType


logger = logging.getLogger(__name__)


class NewsSubscriptionService:
    """新闻订阅和收藏服务"""

    async def list_subscriptions(
            self, db: AsyncSession, user_id: int) -> list[NewsSubscription]:
        """获取用户订阅列表"""
        result = await db.execute(
            select(NewsSubscription)
            .where(NewsSubscription.user_id == user_id)
            .order_by(NewsSubscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_subscription(
            self,
            db: AsyncSession,
            user_id: int,
            category: str | None = None,
            keywords: str | None = None) -> NewsSubscription:
        """创建订阅"""
        subscription = NewsSubscription(
            user_id=user_id,
            category=category,
            keywords=keywords,
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription

    async def delete_subscription(
            self, db: AsyncSession, user_id: int, sub_id: int) -> bool:
        """删除订阅"""
        result = await db.execute(
            select(NewsSubscription).where(
                NewsSubscription.id == sub_id, NewsSubscription.user_id == user_id
            )
        )
        subscription = result.scalar_one_or_none()
        if not subscription:
            return False

        await db.delete(subscription)
        await db.commit()
        return True

    async def get_subscriptions(
            self, db: AsyncSession, user_id: int) -> list[NewsSubscription]:
        """获取用户订阅列表（别名）"""
        return await self.list_subscriptions(db, user_id)

    async def subscribe(
            self,
            db: AsyncSession,
            user_id: int,
            category: str | None = None,
            keywords: str | None = None) -> NewsSubscription:
        """创建订阅（别名）"""
        return await self.create_subscription(db, user_id, category, keywords)

    async def unsubscribe(self, db: AsyncSession,
                          user_id: int, sub_id: int) -> bool:
        """删除订阅（别名）"""
        return await self.delete_subscription(db, user_id, sub_id)

    async def unsubscribe_by_category(
            self, db: AsyncSession, user_id: int, category: str) -> bool:
        """根据类别删除订阅"""
        result = await db.execute(
            select(NewsSubscription).where(
                NewsSubscription.user_id == user_id,
                NewsSubscription.sub_type == "category",
                NewsSubscription.value == category,
            )
        )
        subscription = result.scalar_one_or_none()
        if not subscription:
            return False

        await db.delete(subscription)
        await db.commit()
        return True

    async def get_subscribed_news(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[News], int]:
        """获取订阅的新闻"""
        subscriptions = await self.list_subscriptions(db, user_id)

        if not subscriptions:
            return [], 0

        categories = [
            s.value for s in subscriptions if s.sub_type == "category"]
        keywords_list = [
            json.loads(
                s.value) for s in subscriptions if s.sub_type == "keyword" and s.value]
        keywords = [k for kw in keywords_list for k in kw]

        if not categories and not keywords:
            return [], 0

        query = select(News).where(
            News.is_published,
            News.review_status == "approved",
        )
        count_query = select(func.count(News.id)).where(
            News.is_published,
            News.review_status == "approved",
        )

        if categories:
            query = query.where(News.category.in_(categories))
            count_query = count_query.where(News.category.in_(categories))

        if keywords:
            keyword_conditions = or_(
                *[News.title.ilike(f"%{k}%") for k in keywords])
            query = query.where(keyword_conditions)
            count_query = count_query.where(keyword_conditions)

        query = query.order_by(
            News.published_at.desc()).offset(
            (page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        news_list = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return news_list, total

    async def notify_subscribers_on_publish(
            self, db: AsyncSession, news: News) -> int:
        """发布时通知订阅者"""
        if not news.category:
            return 0

        subscriptions = await db.execute(
            select(NewsSubscription).where(
                NewsSubscription.sub_type == "category",
                NewsSubscription.value == news.category)
        )
        subscriptions = list(subscriptions.scalars().all())

        if not subscriptions:
            return 0

        notified_count = 0
        for sub in subscriptions:
            try:
                notification = Notification(
                    user_id=sub.user_id,
                    notification_type=NotificationType.NEWS,
                    title=f"订阅更新：{news.category}",
                    content=f"您订阅的分类有新内容：{news.title}",
                    data_json=json.dumps(
                        {"news_id": news.id, "category": news.category}),
                )
                db.add(notification)
                notified_count += 1
            except Exception:
                logger.exception("创建订阅通知失败")

        await db.commit()
        return notified_count

    async def toggle_favorite(
        self, db: AsyncSession, news_id: int, user_id: int
    ) -> tuple[bool, int]:
        """切换收藏状态"""
        result = await db.execute(
            select(NewsFavorite).where(
                NewsFavorite.news_id == news_id, NewsFavorite.user_id == user_id
            )
        )
        favorite = result.scalar_one_or_none()

        if favorite:
            await db.delete(favorite)
            await db.commit()
            return False, 0

        favorite = NewsFavorite(news_id=news_id, user_id=user_id)
        db.add(favorite)
        await db.commit()

        count_result = await db.execute(
            select(
                func.count(
                    NewsFavorite.id)).where(
                NewsFavorite.news_id == news_id)
        )
        count = count_result.scalar() or 0

        return True, count

    async def is_favorited(self, db: AsyncSession,
                           news_id: int, user_id: int) -> bool:
        """检查是否已收藏"""
        result = await db.execute(
            select(NewsFavorite).where(
                NewsFavorite.news_id == news_id, NewsFavorite.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_favorite_count(self, db: AsyncSession, news_id: int) -> int:
        """获取收藏数量"""
        result = await db.execute(
            select(
                func.count(
                    NewsFavorite.id)).where(
                NewsFavorite.news_id == news_id)
        )
        return result.scalar() or 0

    async def get_favorite_counts(
            self, db: AsyncSession, news_ids: Sequence[int]) -> dict[int, int]:
        """批量获取收藏数量"""
        if not news_ids:
            return {}

        result = await db.execute(
            select(NewsFavorite.news_id, func.count(NewsFavorite.id))
            .where(NewsFavorite.news_id.in_(news_ids))
            .group_by(NewsFavorite.news_id)
        )
        return {row[0]: int(row[1]) for row in result.all()}

    async def get_favorite_stats(
        self, db: AsyncSession, user_id: int, days: int = 30
    ) -> dict[str, int]:
        """获取收藏统计"""
        start_date = datetime.now() - timedelta(days=days)

        total_result = await db.execute(
            select(
                func.count(
                    NewsFavorite.id)).where(
                NewsFavorite.user_id == user_id)
        )
        total = total_result.scalar() or 0

        recent_result = await db.execute(
            select(func.count(NewsFavorite.id)).where(
                NewsFavorite.user_id == user_id,
                NewsFavorite.created_at >= start_date,
            )
        )
        recent = recent_result.scalar() or 0

        return {"total": total, "recent_30_days": recent}

    async def get_favorited_news_ids(
            self, db: AsyncSession, user_id: int) -> list[int]:
        """获取用户收藏的新闻ID"""
        result = await db.execute(
            select(NewsFavorite.news_id)
            .where(NewsFavorite.user_id == user_id)
            .order_by(NewsFavorite.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_favorites(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[News], int]:
        """获取用户收藏的新闻"""
        query = (
            select(News)
            .join(NewsFavorite, News.id == NewsFavorite.news_id)
            .where(NewsFavorite.user_id == user_id)
            .order_by(NewsFavorite.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        news_list = list(result.scalars().all())

        count_result = await db.execute(
            select(
                func.count(
                    NewsFavorite.id)).where(
                NewsFavorite.user_id == user_id)
        )
        total = count_result.scalar() or 0

        return news_list, total


# 单例
news_subscription_service = NewsSubscriptionService()
