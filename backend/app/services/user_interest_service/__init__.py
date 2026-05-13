"""User interest service."""
from __future__ import annotations
import time
import json
from typing import Optional, Any
from dataclasses import dataclass, field


INTEREST_CATEGORIES: dict[str, list[str]] = {
    "legal": ["法律", "律师", "法规", "诉讼", "仲裁", "司法", "法务", "条文"],
    "family": ["婚姻", "离婚", "抚养", "赡养", "继承", "家暴", "收养", "财产分割"],
    "labor": ["劳动", "工资", "加班", "社保", "工伤", "解雇", "劳动合同", "仲裁"],
    "property": ["房产", "房屋", "买卖", "租赁", "拆迁", "物业", "产权", "过户"],
    "criminal": ["刑事", "犯罪", "辩护", "缓刑", "取保", "自首", "量刑", "减刑"],
    "business": ["公司", "企业", "股东", "股权", "合同", "破产", "并购", "注册"],
    "intellectual": ["专利", "商标", "版权", "侵权", "知识产权", "著作权", "商业秘密", "许可"],
    "traffic": ["交通", "事故", "违章", "赔偿", "驾照", "酒驾", "肇事", "理赔"],
    "debt": ["债务", "借贷", "欠款", "催收", "利息", "担保", "抵押", "执行"],
    "consumer": ["消费", "维权", "退货", "欺诈", "赔偿", "质量", "投诉", "三包"],
}


@dataclass
class UserInterest:
    user_id: int
    categories: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class UserInterestService:
    INTEREST_CATEGORIES = INTEREST_CATEGORIES

    def __init__(self):
        self._interests: dict[int, UserInterest] = {}

    async def get_user_interests(self, user_id: int) -> UserInterest:
        if user_id not in self._interests:
            self._interests[user_id] = UserInterest(user_id=user_id)
        return self._interests[user_id]

    async def update_interests(self, user_id: int, categories: Optional[list[str]] = None, keywords: Optional[list[str]] = None, weights: Optional[dict[str, float]] = None) -> UserInterest:
        interest = await self.get_user_interests(user_id)
        if categories is not None:
            interest.categories = categories
        if keywords is not None:
            interest.keywords = keywords
        if weights is not None:
            interest.weights = weights
        interest.updated_at = time.time()
        return interest

    async def add_interest(self, user_id: int, category: str, weight: float = 1.0) -> UserInterest:
        interest = await self.get_user_interests(user_id)
        if category not in interest.categories:
            interest.categories.append(category)
        interest.weights[category] = weight
        return interest

    async def remove_interest(self, user_id: int, category: str) -> UserInterest:
        interest = await self.get_user_interests(user_id)
        if category in interest.categories:
            interest.categories.remove(category)
        interest.weights.pop(category, None)
        return interest

    @staticmethod
    async def extract_user_interests(db, user_id: int, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
        try:
            from sqlalchemy import select, and_
            from app.models.analytics import UserBehaviorLog
            from datetime import datetime, timezone, timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            stmt = select(UserBehaviorLog).where(
                UserBehaviorLog.user_id == user_id,
                UserBehaviorLog.created_at >= cutoff,
            )
            result = await db.execute(stmt)
            behaviors = result.scalars().all()
        except Exception:
            behaviors = []

        if not behaviors:
            return []

        category_scores: dict[str, dict[str, Any]] = {}
        for behavior in behaviors:
            metadata_str = getattr(behavior, 'metadata_json', '{}') or '{}'
            try:
                metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else {}
            except (json.JSONDecodeError, TypeError):
                metadata = {}
            category = metadata.get("category", "")
            keywords = metadata.get("keywords", [])
            if category:
                if category not in category_scores:
                    category_scores[category] = {"category": category, "score": 0, "matched_keywords": []}
                category_scores[category]["score"] += 1
                if isinstance(keywords, list):
                    category_scores[category]["matched_keywords"].extend(keywords)

        results = sorted(category_scores.values(), key=lambda x: x["score"], reverse=True)
        return results[:limit]

    @staticmethod
    async def get_user_interest_tags(db, user_id: int, days: int = 30) -> list[str]:
        interests = await UserInterestService.extract_user_interests(db, user_id, days=days)
        return [item["category"] for item in interests]

    @staticmethod
    async def get_similar_users(db, user_id: int, limit: int = 10) -> list[int]:
        current_tags = await UserInterestService.get_user_interest_tags(db, user_id)
        if not current_tags:
            return []
        try:
            from sqlalchemy import select, distinct
            from app.models.user import User
            stmt = select(distinct(User.id))
            result = await db.execute(stmt)
            all_user_ids = [row[0] for row in result.all() if row[0] != user_id]
        except Exception:
            all_user_ids = []

        similar = []
        for other_id in all_user_ids:
            other_tags = await UserInterestService.get_user_interest_tags(db, other_id)
            overlap = len(set(current_tags) & set(other_tags))
            if overlap > 0:
                similar.append((other_id, overlap))

        similar.sort(key=lambda x: x[1], reverse=True)
        return [uid for uid, _ in similar[:limit]]


user_interest_service = UserInterestService()
