"""Recommendation service (standalone module)."""
from __future__ import annotations
import time
from typing import Optional

try:
    from app.services.user_interest_service import user_interest_service
except Exception:
    user_interest_service = None


def _generate_lawyer_reason(lawyer, interests: list[str], score: float) -> str:
    rating = getattr(lawyer, 'rating', 0)
    experience_years = getattr(lawyer, 'experience_years', 0)
    specialties = getattr(lawyer, 'specialties', '')
    if rating >= 4.5 and experience_years >= 10:
        return "评分高，资深律师"
    if experience_years >= 5:
        return "经验丰富，擅长" + specialties.split(",")[0] if specialties else "经验丰富"
    for interest in interests:
        if interest and specialties and interest in specialties:
            return f"擅长{interest}"
    return "为您推荐"


def _generate_post_reason(post, interests: list[str], score: float) -> str:
    view_count = getattr(post, 'view_count', 0)
    like_count = getattr(post, 'like_count', 0)
    title = getattr(post, 'title', '')
    content = getattr(post, 'content', '')
    if view_count >= 1000 or like_count >= 50:
        return "热门帖子"
    if like_count >= 20:
        return "高赞内容"
    for interest in interests:
        if interest and (interest in title or interest in content):
            return f"涉及{interest}"
    return "热门帖子"


def _generate_news_reason(news, interests: list[str], score: float) -> str:
    view_count = getattr(news, 'view_count', 0)
    title = getattr(news, 'title', '')
    content = getattr(news, 'content', '')
    if view_count >= 1000:
        return "热门新闻"
    if view_count >= 500:
        return "阅读量高"
    for interest in interests:
        if interest and (interest in title or interest in content):
            return f"关于{interest}"
    return "最新资讯"


class RecommendationService:
    def __init__(self):
        self._user_profiles: dict[int, dict] = {}
        self._recommendations: dict[int, list[dict]] = {}
        self._interactions: list[dict] = []

    async def get_recommendations(self, user_id: int, limit: int = 10, category: Optional[str] = None) -> list[dict]:
        recs = self._recommendations.get(user_id, [])
        if category:
            recs = [r for r in recs if r.get("category") == category]
        return recs[:limit]

    async def update_user_profile(self, user_id: int, interests: Optional[list[str]] = None, preferences: Optional[dict] = None) -> dict:
        profile = self._user_profiles.get(user_id, {"user_id": user_id, "interests": [], "preferences": {}})
        if interests:
            profile["interests"] = interests
        if preferences:
            profile["preferences"].update(preferences)
        self._user_profiles[user_id] = profile
        return profile

    async def track_interaction(self, user_id: int, item_id: str, interaction_type: str = "view") -> dict:
        self._interactions.append({"user_id": user_id, "item_id": item_id, "type": interaction_type, "timestamp": time.time()})
        return {"tracked": True}

    async def get_user_history(self, user_id: int, limit: int = 20) -> list[dict]:
        user_interactions = [i for i in self._interactions if i["user_id"] == user_id]
        return user_interactions[-limit:]

    @staticmethod
    async def recommend_lawyers(db, user_id: int, limit: int = 10) -> list[dict]:
        try:
            from app.services.user_interest_service import user_interest_service
            interests = await user_interest_service.get_user_interest_tags(user_id)
        except Exception:
            interests = []
        result = await db.execute(None)
        lawyers = result.scalars().all() if result else []
        recommendations = []
        for lawyer in lawyers[:limit]:
            reason = _generate_lawyer_reason(lawyer, interests, 0.5)
            recommendations.append({"lawyer": lawyer, "reason": reason})
        return recommendations

    @staticmethod
    async def recommend_posts(db, user_id: int, limit: int = 10) -> list[dict]:
        try:
            from app.services.user_interest_service import user_interest_service
            interests = await user_interest_service.get_user_interest_tags(user_id)
        except Exception:
            interests = []
        result = await db.execute(None)
        posts = result.scalars().all() if result else []
        recommendations = []
        for post in posts[:limit]:
            reason = _generate_post_reason(post, interests, 0.5)
            recommendations.append({"post": post, "reason": reason})
        return recommendations

    @staticmethod
    async def recommend_news(db, user_id: int, limit: int = 10) -> list[dict]:
        try:
            from app.services.user_interest_service import user_interest_service
            interests = await user_interest_service.get_user_interest_tags(user_id)
        except Exception:
            interests = []
        result = await db.execute(None)
        news_items = result.scalars().all() if result else []
        recommendations = []
        for news in news_items[:limit]:
            reason = _generate_news_reason(news, interests, 0.5)
            recommendations.append({"news": news, "reason": reason})
        return recommendations


recommendation_service = RecommendationService()
