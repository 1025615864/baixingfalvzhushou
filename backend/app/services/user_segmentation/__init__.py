"""User segmentation service."""
from __future__ import annotations
import enum
import time
from typing import Optional, Any
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

    def update_user_activity(self, user_id: int, session_duration: int = 0) -> dict:
        if user_id not in self._user_data:
            self._user_data[user_id] = {
                "activity_count": 0,
                "sessions": 0,
                "total_duration": 0,
                "days_since_signup": 0,
            }
        data = self._user_data[user_id]
        data["activity_count"] = data.get("activity_count", 0) + 1
        data["sessions"] = data.get("sessions", 0) + 1
        data["total_duration"] = data.get("total_duration", 0) + session_duration
        return {
            "user_id": user_id,
            "sessions": data["sessions"],
            "lifecycle_stage": self.get_lifecycle_stage(user_id),
        }

    def update_user_data(self, user_id: int, **kwargs) -> None:
        if user_id not in self._user_data:
            self._user_data[user_id] = {}
        self._user_data[user_id].update(kwargs)

    def get_user_data(self, user_id: int) -> dict:
        return self._user_data.get(user_id, {})

    def get_lifecycle_stats(self) -> dict:
        stages = {"new": 0, "onboarding": 0, "active": 0, "casual": 0, "dormant": 0, "inactive": 0}
        for uid in self._user_data:
            stage = self.get_lifecycle_stage(uid)
            stages[stage] = stages.get(stage, 0) + 1
        return {"total_users": len(self._user_data), "stages": stages}


class UserValueSegmenter:
    def __init__(self):
        self._segments: dict[int, str] = {}
        self._value_scores: dict[int, float] = {}

    def calculate_user_value(self, user_id: int, total_spend: float = 0.0, consultation_count: int = 0, activity_score: float = 0.0) -> dict:
        value_score = total_spend * 0.5 + consultation_count * 2 + activity_score * 10
        if value_score >= 100:
            segment = "premium"
        elif value_score >= 50:
            segment = "high"
        elif value_score >= 10:
            segment = "medium"
        else:
            segment = "low"
        self._segments[user_id] = segment
        self._value_scores[user_id] = value_score
        return {
            "user_id": user_id,
            "segment": segment,
            "value_score": value_score,
        }

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

    def get_segment_distribution(self) -> dict:
        segments = {"low": 0, "medium": 0, "high": 0, "premium": 0}
        for segment in self._segments.values():
            if segment in segments:
                segments[segment] += 1
        return {"total_users": len(self._segments), "segments": segments}


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

    async def segment_user(self, user_id: int, total_spend: float = 0.0, consultation_count: int = 0, activity_score: float = 0.0, session_duration: int = 0) -> dict:
        self._lifecycle_manager.update_user_activity(user_id, session_duration=session_duration)
        lifecycle_stage = self._lifecycle_manager.get_lifecycle_stage(user_id)
        value_result = self._value_segmenter.calculate_user_value(
            user_id, total_spend=total_spend, consultation_count=consultation_count, activity_score=activity_score
        )
        return {
            "user_id": user_id,
            "lifecycle_stage": lifecycle_stage,
            "value_segment": value_result["segment"],
            "value_score": value_result["value_score"],
        }

    async def get_segmentation_stats(self) -> dict:
        lifecycle_stats = self._lifecycle_manager.get_lifecycle_stats()
        value_dist = self._value_segmenter.get_segment_distribution()
        return {
            "lifecycle": lifecycle_stats,
            "value_segments": value_dist,
        }

    async def get_recommendations(self, user_id: int) -> dict:
        lifecycle_stage = self._lifecycle_manager.get_lifecycle_stage(user_id)
        value_result = self._value_segmenter.calculate_user_value(user_id, total_spend=0, consultation_count=0, activity_score=0.0)
        recommendations_map = {
            "new": ["引导完成首次咨询", "浏览热门法律问题"],
            "onboarding": ["完善个人资料", "尝试AI法律咨询"],
            "active": ["深度法律咨询", "关注法律动态"],
            "casual": ["推荐热门法律知识", "参与社区讨论"],
            "dormant": ["回归优惠活动", "新功能推荐"],
            "inactive": ["重新激活引导", "热门内容推荐"],
        }
        recommendations = recommendations_map.get(lifecycle_stage, ["浏览法律知识"])
        return {
            "user_id": user_id,
            "lifecycle_stage": lifecycle_stage,
            "value_segment": value_result["segment"],
            "recommendations": recommendations,
        }


user_segmentation_service = UserSegmentationService()
