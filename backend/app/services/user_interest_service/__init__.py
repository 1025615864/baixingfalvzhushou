"""User interest service."""
from __future__ import annotations
import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class UserInterest:
    user_id: int
    categories: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


class UserInterestService:
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

    async def get_similar_users(self, user_id: int, limit: int = 10) -> list[int]:
        interest = await self.get_user_interests(user_id)
        if not interest.categories:
            return []
        scores = []
        for uid, other in self._interests.items():
            if uid == user_id:
                continue
            common = len(set(interest.categories) & set(other.categories))
            if common > 0:
                scores.append((uid, common))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [uid for uid, _ in scores[:limit]]


user_interest_service = UserInterestService()
