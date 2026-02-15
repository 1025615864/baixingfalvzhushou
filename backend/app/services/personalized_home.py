"""个性化首页服务

提供基于用户画像和兴趣推荐的功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class UserProfile:
    """用户画像"""

    def __init__(self):
        self._profiles: dict[int, dict[str, Any]] = {}

    def get_or_create_profile(self, user_id: int) -> dict[str, Any]:
        """获取或创建用户画像

        Args:
            user_id: 用户ID

        Returns:
            用户画像
        """
        if user_id not in self._profiles:
            self._profiles[user_id] = {
                "user_id": user_id,
                "interests": [],
                "browse_history": [],
                "preferences": {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        return self._profiles[user_id]

    def update_interests(
        self,
        user_id: int,
        interests: list[str],
    ) -> dict[str, Any]:
        """更新兴趣标签

        Args:
            user_id: 用户ID
            interests: 兴趣列表

        Returns:
            更新结果
        """
        profile = self.get_or_create_profile(user_id)
        profile["interests"] = interests
        profile["updated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Updated interests for user {user_id}: {interests}")

        return {
            "success": True,
            "interests": interests,
        }

    def add_browse_history(
        self,
        user_id: int,
        item_id: str,
        category: str,
    ) -> dict[str, Any]:
        """添加浏览历史

        Args:
            user_id: 用户ID
            item_id: 内容ID
            category: 分类

        Returns:
            添加结果
        """
        profile = self.get_or_create_profile(user_id)
        profile["browse_history"].append({
            "item_id": item_id,
            "category": category,
            "viewed_at": datetime.now(timezone.utc).isoformat(),
        })

        if len(profile["browse_history"]) > 100:
            profile["browse_history"] = profile["browse_history"][-100:]

        profile["updated_at"] = datetime.now(timezone.utc).isoformat()

        return {
            "success": True,
            "history_count": len(profile["browse_history"]),
        }

    def get_user_profile(self, user_id: int) -> dict[str, Any]:
        """获取用户画像

        Args:
            user_id: 用户ID

        Returns:
            用户画像
        """
        return self.get_or_create_profile(user_id)


class InterestRecommender:
    """兴趣推荐器"""

    def __init__(self):
        self._items: dict[str, dict[str, Any]] = {}
        self._recommendations: dict[int, list[dict[str, Any]]] = {}

    def register_item(
        self,
        item_id: str,
        title: str,
        category: str,
        tags: list[str],
        score: float = 0.5,
    ) -> dict[str, Any]:
        """注册内容项

        Args:
            item_id: 内容ID
            title: 标题
            category: 分类
            tags: 标签
            score: 评分

        Returns:
            注册结果
        """
        self._items[item_id] = {
            "id": item_id,
            "title": title,
            "category": category,
            "tags": tags,
            "score": score,
            "view_count": 0,
        }

        return {
            "item_id": item_id,
            "registered": True,
        }

    def recommend(
        self,
        user_id: int,
        interests: list[str],
        browse_history: list[dict[str, Any]],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """推荐内容

        Args:
            user_id: 用户ID
            interests: 兴趣列表
            browse_history: 浏览历史
            limit: 推荐数量

        Returns:
            推荐列表
        """
        history_categories = set(h["category"] for h in browse_history)
        history_items = set(h["item_id"] for h in browse_history)

        candidates: list[dict[str, Any]] = []

        for item_id, item in self._items.items():
            if item_id in history_items:
                continue

            relevance_score = 0.0

            for tag in item["tags"]:
                if tag in interests:
                    relevance_score += 0.3

            if item["category"] in history_categories:
                relevance_score += 0.2

            relevance_score += item["score"] * 0.3

            if relevance_score > 0:
                candidates.append({
                    **item,
                    "relevance_score": round(relevance_score, 3),
                })

        candidates.sort(key=lambda x: x["relevance_score"], reverse=True)

        recommendations = candidates[:limit]

        self._recommendations[user_id] = recommendations

        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")

        return recommendations

    def track_click(
        self,
        user_id: int,
        item_id: str,
    ) -> dict[str, Any]:
        """追踪点击

        Args:
            user_id: 用户ID
            item_id: 内容ID

        Returns:
            追踪结果
        """
        if item_id in self._items:
            self._items[item_id]["view_count"] = self._items[item_id].get(
                "view_count", 0) + 1

        return {
            "success": True,
            "item_id": item_id,
        }


class PersonalizedHomeService:
    """个性化首页服务"""

    def __init__(self):
        self.user_profile = UserProfile()
        self.interest_recommender = InterestRecommender()

    async def get_personalized_home(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        """获取个性化首页

        Args:
            user_id: 用户ID

        Returns:
            首页数据
        """
        profile = self.user_profile.get_user_profile(user_id)

        recommendations = self.interest_recommender.recommend(
            user_id=user_id,
            interests=profile["interests"],
            browse_history=profile["browse_history"],
            limit=10,
        )

        return {
            "user_id": user_id,
            "profile": {
                "interests": profile["interests"],
                "history_count": len(profile["browse_history"]),
            },
            "recommendations": recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def update_user_interests(
        self,
        user_id: int,
        interests: list[str],
    ) -> dict[str, Any]:
        """更新用户兴趣

        Args:
            user_id: 用户ID
            interests: 兴趣列表

        Returns:
            更新结果
        """
        result = self.user_profile.update_interests(user_id, interests)

        return {
            **result,
            "profile": self.user_profile.get_user_profile(user_id),
        }

    async def track_content_view(
        self,
        user_id: int,
        item_id: str,
        category: str,
    ) -> dict[str, Any]:
        """追踪内容浏览

        Args:
            user_id: 用户ID
            item_id: 内容ID
            category: 分类

        Returns:
            追踪结果
        """
        history_result = self.user_profile.add_browse_history(
            user_id, item_id, category)
        self.interest_recommender.track_click(user_id, item_id)

        return {
            "success": True,
            "history_count": history_result["history_count"],
        }

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计数据
        """
        total_users = len(self.user_profile._profiles)
        users_with_interests = sum(
            1 for p in self.user_profile._profiles.values()
            if p["interests"]
        )

        total_recommendations = sum(
            len(r) for r in self.interest_recommender._recommendations.values()
        )

        return {
            "total_users": total_users,
            "users_with_interests": users_with_interests,
            "interest_adoption_rate": round(users_with_interests / max(total_users, 1) * 100, 2),
            "total_recommendations": total_recommendations,
        }


# 单例实例
personalized_home_service = PersonalizedHomeService()


async def get_personalized_home(user_id: int) -> dict[str, Any]:
    """便捷函数：获取个性化首页

    Args:
        user_id: 用户ID

    Returns:
        首页数据
    """
    return await personalized_home_service.get_personalized_home(user_id=user_id)


async def update_user_interests(
    user_id: int,
    interests: list[str],
) -> dict[str, Any]:
    """便捷函数：更新用户兴趣

    Args:
        user_id: 用户ID
        interests: 兴趣列表

    Returns:
        更新结果
    """
    return await personalized_home_service.update_user_interests(
        user_id=user_id,
        interests=interests,
    )


async def track_content_view(
    user_id: int,
    item_id: str,
    category: str,
) -> dict[str, Any]:
    """便捷函数：追踪内容浏览

    Args:
        user_id: 用户ID
        item_id: 内容ID
        category: 分类

    Returns:
        追踪结果
    """
    return await personalized_home_service.track_content_view(
        user_id=user_id,
        item_id=item_id,
        category=category,
    )
