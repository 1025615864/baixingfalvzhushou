"""推荐服务 - 服务层"""
import logging
import random
from typing import List, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserFeature, ItemFeature

logger = logging.getLogger(__name__)


class RecommendationService:
    """推荐服务 - 基于用户特征的个性化推荐"""

    async def recommend_lawyers(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> List[Dict]:
        """推荐律师"""
        # 获取用户特征
        user_features = await self._get_user_features(session, user_id)

        # 基于用户兴趣标签推荐律师
        # 这里应该是实际推荐算法，目前使用模拟数据
        items = [
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

        return items

    async def recommend_news(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> List[Dict]:
        """推荐新闻"""
        # 获取用户特征
        user_features = await self._get_user_features(session, user_id)

        # 基于用户浏览历史推荐新闻
        items = [
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

        return items

    async def recommend_posts(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 10,
    ) -> List[Dict]:
        """推荐帖子"""
        # 获取用户特征
        user_features = await self._get_user_features(session, user_id)

        # 基于用户兴趣推荐帖子
        items = [
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

        return items

    async def get_personalized_feed(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 20,
    ) -> List[Dict]:
        """个性化推荐信息流（混合推荐）"""
        news_items = await self.recommend_news(session, user_id, limit // 2)
        post_items = await self.recommend_posts(session, user_id, limit // 2)
        lawyer_items = await self.recommend_lawyers(session, user_id, limit // 4)

        # 混合并排序
        all_items = news_items + post_items + lawyer_items
        all_items.sort(key=lambda x: x.get("score", 0), reverse=True)

        return all_items[:limit]

    async def update_user_features(
        self,
        session: AsyncSession,
        user_id: int,
        features: Dict,
    ) -> UserFeature:
        """更新用户特征"""
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
        return user_feature

    async def _get_user_features(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> Optional[Dict]:
        """获取用户特征"""
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
        """更新物品特征"""
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


recommendation_service = RecommendationService()
