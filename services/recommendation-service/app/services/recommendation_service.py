import logging
from typing import List, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserFeature, ItemFeature
from app.services.client_service import microservice_client
from app.services.cache_service import redis_cache_service

logger = logging.getLogger(__name__)


class RecommendationService:

    async def recommend_lawyers(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> List[Dict]:
        cache_key = f"rec:lawyers:{user_id}:{limit}"
        cached = await redis_cache_service.get(cache_key)
        if cached is not None:
            return cached

        user_features = await self._get_user_features(session, user_id)
        items = await microservice_client.fetch_lawyers(user_id, limit)

        if not items:
            items = await self._fallback_lawyers(user_features, limit)

        for item in items:
            item.setdefault("type", "lawyer")

        await redis_cache_service.set(cache_key, items)
        return items

    async def recommend_news(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> List[Dict]:
        cache_key = f"rec:news:{user_id}:{limit}"
        cached = await redis_cache_service.get(cache_key)
        if cached is not None:
            return cached

        user_features = await self._get_user_features(session, user_id)
        items = await microservice_client.fetch_news(user_id, limit)

        if not items:
            items = await self._fallback_news(user_features, limit)

        for item in items:
            item.setdefault("type", "news")

        await redis_cache_service.set(cache_key, items)
        return items

    async def recommend_posts(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> List[Dict]:
        cache_key = f"rec:posts:{user_id}:{limit}"
        cached = await redis_cache_service.get(cache_key)
        if cached is not None:
            return cached

        user_features = await self._get_user_features(session, user_id)
        items = await microservice_client.fetch_posts(user_id, limit)

        if not items:
            items = await self._fallback_posts(user_features, limit)

        for item in items:
            item.setdefault("type", "post")

        await redis_cache_service.set(cache_key, items)
        return items

    async def recommend_knowledge(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> List[Dict]:
        cache_key = f"rec:knowledge:{user_id}:{limit}"
        cached = await redis_cache_service.get(cache_key)
        if cached is not None:
            return cached

        items = await microservice_client.fetch_knowledge(user_id, limit)

        for item in items:
            item.setdefault("type", "knowledge")

        await redis_cache_service.set(cache_key, items)
        return items

    async def recommend_homepage(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 20,
    ) -> List[Dict]:
        cache_key = f"rec:homepage:{user_id}:{limit}"
        cached = await redis_cache_service.get(cache_key)
        if cached is not None:
            return cached

        lawyer_limit = max(limit // 4, 1)
        news_limit = max(limit // 3, 1)
        post_limit = max(limit // 3, 1)
        knowledge_limit = max(limit // 6, 1)

        lawyers = await self.recommend_lawyers(session, user_id, lawyer_limit)
        news = await self.recommend_news(session, user_id, news_limit)
        posts = await self.recommend_posts(session, user_id, post_limit)
        knowledge = await self.recommend_knowledge(session, user_id, knowledge_limit)

        all_items = lawyers + news + posts + knowledge
        all_items.sort(key=lambda x: x.get("score", 0), reverse=True)

        result = all_items[:limit]
        await redis_cache_service.set(cache_key, result, ttl=120)
        return result

    async def get_personalized_feed(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 20,
    ) -> List[Dict]:
        cache_key = f"rec:feed:{user_id}:{limit}"
        cached = await redis_cache_service.get(cache_key)
        if cached is not None:
            return cached

        news_items = await self.recommend_news(session, user_id, limit // 2)
        post_items = await self.recommend_posts(session, user_id, limit // 2)
        lawyer_items = await self.recommend_lawyers(session, user_id, limit // 4)

        all_items = news_items + post_items + lawyer_items
        all_items.sort(key=lambda x: x.get("score", 0), reverse=True)

        result = all_items[:limit]
        await redis_cache_service.set(cache_key, result)
        return result

    async def update_user_features(
        self,
        session: AsyncSession,
        user_id: int,
        features: Dict,
    ) -> UserFeature:
        query = select(UserFeature).where(UserFeature.user_id == user_id)
        result = await session.execute(query)
        user_feature = result.scalar_one_or_none()

        if user_feature:
            user_feature.features.update(features)
        else:
            user_feature = UserFeature(
                user_id=user_id,
                features=features,
            )
            session.add(user_feature)

        await session.flush()
        await redis_cache_service.delete_pattern(f"rec:*:{user_id}:*")
        return user_feature

    async def _get_user_features(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> Optional[Dict]:
        query = select(UserFeature).where(UserFeature.user_id == user_id)
        result = await session.execute(query)
        user_feature = result.scalar_one_or_none()

        return user_feature.features if user_feature else {}

    async def update_item_features(
        self,
        session: AsyncSession,
        item_type: str,
        item_id: int,
        features: Dict,
        score: float = 0.0,
    ) -> ItemFeature:
        from sqlalchemy import select
        query = select(ItemFeature).where(
            ItemFeature.item_type == item_type,
            ItemFeature.item_id == item_id,
        )
        result = await session.execute(query)
        item_feature = result.scalar_one_or_none()

        if item_feature:
            item_feature.features.update(features)
            item_feature.score = score
        else:
            item_feature = ItemFeature(
                item_type=item_type,
                item_id=item_id,
                features=features,
                score=score,
            )
            session.add(item_feature)

        await session.flush()
        return item_feature

    async def _fallback_lawyers(self, user_features: Optional[Dict], limit: int) -> List[Dict]:
        return [
            {
                "id": i,
                "type": "lawyer",
                "title": f"推荐律师 {i}",
                "description": "资深律师，专业可靠",
                "url": f"/lawyer/{i}",
                "score": round(0.9 - i * 0.05, 2),
            }
            for i in range(1, min(limit + 1, 4))
        ]

    async def _fallback_news(self, user_features: Optional[Dict], limit: int) -> List[Dict]:
        return [
            {
                "id": i,
                "type": "news",
                "title": f"推荐新闻 {i}",
                "description": "最新法律资讯",
                "url": f"/news/{i}",
                "score": round(0.85 - i * 0.03, 2),
            }
            for i in range(1, min(limit + 1, 5))
        ]

    async def _fallback_posts(self, user_features: Optional[Dict], limit: int) -> List[Dict]:
        return [
            {
                "id": i,
                "type": "post",
                "title": f"推荐帖子 {i}",
                "description": "热门法律讨论",
                "url": f"/forum/{i}",
                "score": round(0.8 - i * 0.04, 2),
            }
            for i in range(1, min(limit + 1, 5))
        ]


recommendation_service = RecommendationService()
