"""用户分层运营服务

提供用户生命周期管理和价值分层功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class UserLifecycleManager:
    """用户生命周期管理器"""

    def __init__(self):
        self._users: dict[int, dict[str, Any]] = {}

    def get_lifecycle_stage(self, user_id: int) -> str:
        """获取用户生命周期阶段

        Args:
            user_id: 用户ID

        Returns:
            生命周期阶段
        """
        if user_id not in self._users:
            return "new"

        user = self._users[user_id]
        days_since_registration = (
            datetime.now(
                timezone.utc) -
            datetime.fromisoformat(
                user["registered_at"])).days
        last_active_days = (
            datetime.now(
                timezone.utc) -
            datetime.fromisoformat(
                user["last_active_at"])).days

        if days_since_registration <= 7:
            return "new"
        elif last_active_days > 30:
            return "churned"
        elif user.get("sessions", 0) < 3:
            return "activation"
        elif last_active_days <= 7:
            return "active"
        else:
            return "dormant"

    def update_user_activity(
        self,
        user_id: int,
        session_duration: int = 0,
    ) -> dict[str, Any]:
        """更新用户活动

        Args:
            user_id: 用户ID
            session_duration: 会话时长（秒）

        Returns:
            更新结果
        """
        if user_id not in self._users:
            self._users[user_id] = {
                "user_id": user_id,
                "registered_at": datetime.now(timezone.utc).isoformat(),
                "sessions": 0,
                "total_duration": 0,
                "last_active_at": datetime.now(timezone.utc).isoformat(),
            }

        self._users[user_id]["sessions"] = self._users[user_id].get(
            "sessions", 0) + 1
        self._users[user_id]["total_duration"] = self._users[user_id].get(
            "total_duration", 0) + session_duration
        self._users[user_id]["last_active_at"] = datetime.now(
            timezone.utc).isoformat()

        stage = self.get_lifecycle_stage(user_id)
        self._users[user_id]["lifecycle_stage"] = stage

        logger.info(f"User {user_id} lifecycle stage: {stage}")

        return {
            "user_id": user_id,
            "lifecycle_stage": stage,
            "sessions": self._users[user_id]["sessions"],
        }

    def get_lifecycle_stats(self) -> dict[str, Any]:
        """获取生命周期统计

        Returns:
            统计数据
        """
        stages = {
            "new": 0,
            "activation": 0,
            "active": 0,
            "dormant": 0,
            "churned": 0,
        }

        for user_id in self._users:
            stage = self.get_lifecycle_stage(user_id)
            stages[stage] = stages.get(stage, 0) + 1

        return {
            "total_users": len(self._users),
            "stages": stages,
        }


class UserValueSegmenter:
    """用户价值分层器"""

    def __init__(self):
        self._segments: dict[int, dict[str, Any]] = {}

    def calculate_user_value(
        self,
        user_id: int,
        total_spend: float = 0,
        consultation_count: int = 0,
        activity_score: float = 0.0,
    ) -> dict[str, Any]:
        """计算用户价值

        Args:
            user_id: 用户ID
            total_spend: 总消费
            consultation_count: 咨询次数
            activity_score: 活跃度评分

        Returns:
            价值分层结果
        """
        value_score = (
            total_spend * 0.5 +
            consultation_count * 2 +
            activity_score * 10
        )

        if value_score >= 100:
            segment = "premium"
        elif value_score >= 50:
            segment = "high"
        elif value_score >= 20:
            segment = "medium"
        else:
            segment = "low"

        self._segments[user_id] = {
            "user_id": user_id,
            "value_score": round(value_score, 2),
            "segment": segment,
            "total_spend": total_spend,
            "consultation_count": consultation_count,
            "activity_score": activity_score,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "user_id": user_id,
            "value_score": round(value_score, 2),
            "segment": segment,
        }

    def get_segment_distribution(self) -> dict[str, Any]:
        """获取分段分布

        Returns:
            分段统计
        """
        segments = {"premium": 0, "high": 0, "medium": 0, "low": 0}

        for user_id, data in self._segments.items():
            segment = data.get("segment", "low")
            segments[segment] = segments.get(segment, 0) + 1

        return {
            "total_users": len(self._segments),
            "segments": segments,
        }


class UserSegmentationService:
    """用户分层运营服务"""

    def __init__(self):
        self.lifecycle_manager = UserLifecycleManager()
        self.value_segmenter = UserValueSegmenter()

    async def segment_user(
        self,
        user_id: int,
        total_spend: float = 0,
        consultation_count: int = 0,
        activity_score: float = 0.0,
        session_duration: int = 0,
    ) -> dict[str, Any]:
        """用户分层

        Args:
            user_id: 用户ID
            total_spend: 总消费
            consultation_count: 咨询次数
            activity_score: 活跃度评分
            session_duration: 会话时长

        Returns:
            分层结果
        """
        lifecycle_result = self.lifecycle_manager.update_user_activity(
            user_id=user_id,
            session_duration=session_duration,
        )

        value_result = self.value_segmenter.calculate_user_value(
            user_id=user_id,
            total_spend=total_spend,
            consultation_count=consultation_count,
            activity_score=activity_score,
        )

        return {
            "user_id": user_id,
            "lifecycle_stage": lifecycle_result["lifecycle_stage"],
            "value_segment": value_result["segment"],
            "value_score": value_result["value_score"],
        }

    async def get_segmentation_stats(self) -> dict[str, Any]:
        """获取分层统计

        Returns:
            统计数据
        """
        lifecycle_stats = self.lifecycle_manager.get_lifecycle_stats()
        segment_stats = self.value_segmenter.get_segment_distribution()

        return {
            "lifecycle": lifecycle_stats,
            "value_segments": segment_stats,
        }

    async def get_recommendations(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        """获取运营建议

        Args:
            user_id: 用户ID

        Returns:
            运营建议
        """
        lifecycle_stage = self.lifecycle_manager.get_lifecycle_stage(user_id)
        value_segment = self.value_segmenter._segments.get(
            user_id, {}).get("segment", "low")

        recommendations = []

        if lifecycle_stage == "new":
            recommendations.extend([
                "发送欢迎邮件",
                "引导完成首次咨询",
                "提供新手引导",
            ])
        elif lifecycle_stage == "activation":
            recommendations.extend([
                "推送热门咨询案例",
                "提供限时优惠",
                "邀请参与互动",
            ])
        elif lifecycle_stage == "active":
            recommendations.extend([
                "推荐高级功能",
                "邀请成为会员",
                "提供个性化内容",
            ])
        elif lifecycle_stage == "dormant":
            recommendations.extend([
                "发送召回通知",
                "提供专属优惠",
                "推送新功能介绍",
            ])
        elif lifecycle_stage == "churned":
            recommendations.extend([
                "发送调查问卷",
                "提供大额召回优惠",
                "邀请参与满意度调研",
            ])

        if value_segment == "premium":
            recommendations.append("提供专属客服")
        elif value_segment == "high":
            recommendations.append("推荐增值服务")

        return {
            "user_id": user_id,
            "lifecycle_stage": lifecycle_stage,
            "value_segment": value_segment,
            "recommendations": recommendations,
        }


# 单例实例
segmentation_service = UserSegmentationService()


async def segment_user(
    user_id: int,
    total_spend: float = 0,
    consultation_count: int = 0,
    activity_score: float = 0.0,
    session_duration: int = 0,
) -> dict[str, Any]:
    """便捷函数：用户分层

    Args:
        user_id: 用户ID
        total_spend: 总消费
        consultation_count: 咨询次数
        activity_score: 活跃度评分
        session_duration: 会话时长

    Returns:
        分层结果
    """
    return await segmentation_service.segment_user(
        user_id=user_id,
        total_spend=total_spend,
        consultation_count=consultation_count,
        activity_score=activity_score,
        session_duration=session_duration,
    )


async def get_segmentation_stats() -> dict[str, Any]:
    """便捷函数：获取分层统计

    Returns:
        统计数据
    """
    return await segmentation_service.get_segmentation_stats()


async def get_recommendations(user_id: int) -> dict[str, Any]:
    """便捷函数：获取运营建议

    Args:
        user_id: 用户ID

    Returns:
        运营建议
    """
    return await segmentation_service.get_recommendations(user_id=user_id)
