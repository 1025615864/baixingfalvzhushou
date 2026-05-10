"""User segmentation service."""
from __future__ import annotations
import enum
import time
from typing import Optional
from dataclasses import dataclass, field


class UserSegment(enum.Enum):
    NEW_USER = "new_user"
    ACTIVE_USER = "active_user"
    PREMIUM_USER = "premium_user"
    INACTIVE_USER = "inactive_user"
    VIP_USER = "vip_user"


@dataclass
class UserSegmentInfo:
    user_id: int
    segment: UserSegment = UserSegment.NEW_USER
    score: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class UserLifecycleManager:
    def __init__(self):
        self._user_data: dict[int, dict] = {}

    def get_lifecycle_stage(self, user_id: int) -> str:
        data = self._user_data.get(user_id, {})
        if not data:
            return "new"
        activity = data.get("activity_count", 0)
        days_since_signup = data.get("days_since_signup", 0)
        if days_since_signup <= 7:
            return "onboarding"
        if activity >= 10:
            return "active"
        if activity > 0:
            return "casual"
        if days_since_signup > 30:
            return "dormant"
        return "inactive"

    def update_user_data(self, user_id: int, **kwargs) -> None:
        if user_id not in self._user_data:
            self._user_data[user_id] = {}
        self._user_data[user_id].update(kwargs)

    def get_user_data(self, user_id: int) -> dict:
        return self._user_data.get(user_id, {})


class UserValueSegmenter:
    def __init__(self):
        self._segments: dict[int, str] = {}

    def segment_user(self, user_id: int, total_spent: float = 0.0, activity_score: float = 0.0) -> str:
        if total_spent >= 1000:
            segment = "high_value"
        elif total_spent >= 100:
            segment = "medium_value"
        elif activity_score >= 50:
            segment = "potential_value"
        else:
            segment = "low_value"
        self._segments[user_id] = segment
        return segment

    def get_segment(self, user_id: int) -> Optional[str]:
        return self._segments.get(user_id)

    def get_users_by_segment(self, segment: str) -> list[int]:
        return [uid for uid, s in self._segments.items() if s == segment]


class UserSegmentationService:
    def __init__(self):
        self._segments: dict[int, UserSegmentInfo] = {}
        self._lifecycle_manager = UserLifecycleManager()
        self._value_segmenter = UserValueSegmenter()

    async def get_user_segment(self, user_id: int) -> UserSegmentInfo:
        if user_id not in self._segments:
            self._segments[user_id] = UserSegmentInfo(user_id=user_id)
        return self._segments[user_id]

    async def update_segment(self, user_id: int, segment: UserSegment, score: Optional[float] = None, tags: Optional[list[str]] = None) -> UserSegmentInfo:
        info = await self.get_user_segment(user_id)
        info.segment = segment
        if score is not None:
            info.score = score
        if tags is not None:
            info.tags = tags
        return info

    async def get_users_by_segment(self, segment: UserSegment) -> list[UserSegmentInfo]:
        return [info for info in self._segments.values() if info.segment == segment]

    async def auto_classify(self, user_id: int, activity_score: float = 0.0, purchase_amount: float = 0.0) -> UserSegmentInfo:
        if purchase_amount >= 1000:
            segment = UserSegment.VIP_USER
        elif purchase_amount > 0:
            segment = UserSegment.PREMIUM_USER
        elif activity_score >= 50:
            segment = UserSegment.ACTIVE_USER
        elif activity_score > 0:
            segment = UserSegment.NEW_USER
        else:
            segment = UserSegment.INACTIVE_USER
        return await self.update_segment(user_id, segment, score=activity_score)

    async def get_segment_stats(self) -> dict:
        stats = {}
        for segment in UserSegment:
            stats[segment.value] = sum(1 for info in self._segments.values() if info.segment == segment)
        return stats


user_segmentation_service = UserSegmentationService()
