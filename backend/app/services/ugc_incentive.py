"""用户生成内容（UGC）激励体系服务

提供内容贡献量化和激励可配置功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ContentContributionTracker:
    """内容贡献追踪器"""

    def __init__(self):
        self._contributions: dict[int, dict[str, Any]] = {}

    def reset(self) -> None:
        """重置追踪器状态（用于测试隔离）"""
        self._contributions.clear()

    def record_contribution(
        self,
        user_id: int,
        content_type: str,
        content_id: str,
        quality_score: float = 0.5,
    ) -> dict[str, Any]:
        """记录贡献

        Args:
            user_id: 用户ID
            content_type: 内容类型
            content_id: 内容ID
            quality_score: 质量评分

        Returns:
            记录结果
        """
        if user_id not in self._contributions:
            self._contributions[user_id] = {
                "user_id": user_id,
                "total_contributions": 0,
                "content_types": {},
                "total_quality_score": 0,
                "last_contribution_at": None,
            }

        user_data = self._contributions[user_id]
        user_data["total_contributions"] += 1
        user_data["total_quality_score"] += quality_score

        if content_type not in user_data["content_types"]:
            user_data["content_types"][content_type] = {
                "count": 0,
                "content_ids": [],
            }

        user_data["content_types"][content_type]["count"] += 1
        user_data["content_types"][content_type]["content_ids"].append(
            content_id)
        user_data["last_contribution_at"] = datetime.now(
            timezone.utc).isoformat()

        logger.info(
            f"Recorded contribution for user {user_id}: {content_type}")

        return {
            "user_id": user_id,
            "content_type": content_type,
            "total_contributions": user_data["total_contributions"],
            "average_quality": round(
                user_data["total_quality_score"] /
                user_data["total_contributions"],
                2),
        }

    def get_user_contributions(self, user_id: int) -> dict[str, Any]:
        """获取用户贡献

        Args:
            user_id: 用户ID

        Returns:
            贡献数据
        """
        if user_id not in self._contributions:
            return {
                "user_id": user_id,
                "total_contributions": 0,
                "content_types": {},
                "average_quality": 0,
            }

        user_data = self._contributions[user_id]
        avg_quality = round(
            user_data["total_quality_score"] /
            user_data["total_contributions"],
            2) if user_data["total_contributions"] > 0 else 0

        return {
            "user_id": user_id,
            "total_contributions": user_data["total_contributions"],
            "content_types": user_data["content_types"],
            "average_quality": avg_quality,
            "last_contribution_at": user_data["last_contribution_at"],
        }

    def get_leaderboard(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取排行榜

        Args:
            limit: 限制数量

        Returns:
            排行榜
        """
        sorted_users = sorted(
            self._contributions.items(),
            key=lambda x: x[1]["total_contributions"],
            reverse=True,
        )

        leaderboard = []
        for i, (user_id, data) in enumerate(sorted_users[:limit]):
            avg_quality = round(
                data["total_quality_score"] /
                data["total_contributions"],
                2) if data["total_contributions"] > 0 else 0
            leaderboard.append({
                "rank": i + 1,
                "user_id": user_id,
                "total_contributions": data["total_contributions"],
                "average_quality": avg_quality,
            })

        return leaderboard


class IncentiveConfigurator:
    """激励配置器"""

    def __init__(self):
        self._rules: dict[str, dict[str, Any]] = {}

    def reset(self) -> None:
        """重置配置器状态（用于测试隔离）"""
        self._rules.clear()

    def configure_incentive(
        self,
        incentive_type: str,
        points_per_unit: int,
        bonus_threshold: int | None = None,
        bonus_multiplier: float | None = None,
    ) -> dict[str, Any]:
        """配置激励

        Args:
            incentive_type: 激励类型
            points_per_unit: 每单位积分
            bonus_threshold: 奖励阈值
            bonus_multiplier: 奖励倍数

        Returns:
            配置结果
        """
        self._rules[incentive_type] = {
            "type": incentive_type,
            "points_per_unit": points_per_unit,
            "bonus_threshold": bonus_threshold,
            "bonus_multiplier": bonus_multiplier,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "type": incentive_type,
            "points_per_unit": points_per_unit,
            "configured": True,
        }

    def calculate_rewards(
        self,
        user_id: int,
        contributions: dict[str, int] | dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """计算奖励

        Args:
            user_id: 用户ID
            contributions: 贡献数据（格式: {"article": 1} 或 {"article": {"count": 1, ...}}）

        Returns:
            奖励数据
        """
        total_points = 0
        breakdown = {}

        for content_type, data in contributions.items():
            count = data["count"] if isinstance(data, dict) else data
            rule = self._rules.get(content_type, {"points_per_unit": 10})
            points = count * rule["points_per_unit"]

            if rule.get(
                    "bonus_threshold") and count >= rule["bonus_threshold"]:
                points = int(points * rule.get("bonus_multiplier", 1.5))

            breakdown[content_type] = {
                "count": count,
                "base_points": count * rule["points_per_unit"],
                "bonus_points": points - count * rule["points_per_unit"],
                "total_points": points,
            }

            total_points += points

        return {
            "user_id": user_id,
            "total_points": total_points,
            "breakdown": breakdown,
        }

    def get_incentive_rules(self) -> dict[str, dict[str, Any]]:
        """获取激励规则

        Returns:
            规则列表
        """
        return self._rules


class UGCIncentiveService:
    """UGC 激励服务"""

    def __init__(self):
        self.contribution_tracker = ContentContributionTracker()
        self.incentive_configurator = IncentiveConfigurator()

        self._configure_default_rules()

    def reset(self) -> None:
        """重置服务状态（用于测试隔离）"""
        self.contribution_tracker.reset()
        self.incentive_configurator.reset()
        self._configure_default_rules()

    def _configure_default_rules(self) -> None:
        """配置默认规则"""
        default_rules = {
            "article": {"points_per_unit": 20, "bonus_threshold": 5, "bonus_multiplier": 1.5},
            "comment": {"points_per_unit": 5, "bonus_threshold": 10, "bonus_multiplier": 1.2},
            "answer": {"points_per_unit": 15, "bonus_threshold": 3, "bonus_multiplier": 1.3},
            "review": {"points_per_unit": 10, "bonus_threshold": 5, "bonus_multiplier": 1.5},
        }

        for rule_type, config in default_rules.items():
            self.incentive_configurator.configure_incentive(
                incentive_type=rule_type,
                points_per_unit=config["points_per_unit"],
                bonus_threshold=config.get("bonus_threshold"),
                bonus_multiplier=config.get("bonus_multiplier"),
            )

    async def record_content(
        self,
        user_id: int,
        content_type: str,
        content_id: str,
        quality_score: float = 0.5,
    ) -> dict[str, Any]:
        """记录内容

        Args:
            user_id: 用户ID
            content_type: 内容类型
            content_id: 内容ID
            quality_score: 质量评分

        Returns:
            记录结果
        """
        contribution_result = self.contribution_tracker.record_contribution(
            user_id=user_id,
            content_type=content_type,
            content_id=content_id,
            quality_score=quality_score,
        )

        user_contributions = self.contribution_tracker.get_user_contributions(
            user_id)
        rewards = self.incentive_configurator.calculate_rewards(
            user_id=user_id,
            contributions={content_type: 1},
        )

        return {
            **contribution_result,
            "rewards": rewards,
        }

    async def get_user_stats(self, user_id: int) -> dict[str, Any]:
        """获取用户统计

        Args:
            user_id: 用户ID

        Returns:
            统计数据
        """
        contributions = self.contribution_tracker.get_user_contributions(
            user_id)
        rewards = self.incentive_configurator.calculate_rewards(
            user_id=user_id,
            contributions=contributions.get("content_types", {}),
        )

        return {
            "user_id": user_id,
            "contributions": contributions,
            "total_points": rewards["total_points"],
            "incentive_rules": self.incentive_configurator.get_incentive_rules(),
        }

    async def get_leaderboard(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取排行榜

        Args:
            limit: 限制数量

        Returns:
            排行榜
        """
        return self.contribution_tracker.get_leaderboard(limit)

    async def get_stats(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计数据
        """
        total_contributions = sum(u["total_contributions"]
                                  for u in self.contribution_tracker._contributions.values())

        return {
            "total_users": len(self.contribution_tracker._contributions),
            "total_contributions": total_contributions,
            "incentive_rules_count": len(self.incentive_configurator._rules),
        }


# 单例实例
ugc_incentive_service = UGCIncentiveService()


def reset_ugc_incentive_service() -> None:
    """重置UGC激励服务状态（用于测试隔离）"""
    ugc_incentive_service.reset()


async def record_content(
    user_id: int,
    content_type: str,
    content_id: str,
    quality_score: float = 0.5,
) -> dict[str, Any]:
    """便捷函数：记录内容

    Args:
        user_id: 用户ID
        content_type: 内容类型
        content_id: 内容ID
        quality_score: 质量评分

    Returns:
        记录结果
    """
    return await ugc_incentive_service.record_content(
        user_id=user_id,
        content_type=content_type,
        content_id=content_id,
        quality_score=quality_score,
    )


async def get_user_stats(user_id: int) -> dict[str, Any]:
    """便捷函数：获取用户统计

    Args:
        user_id: 用户ID

    Returns:
        统计数据
    """
    return await ugc_incentive_service.get_user_stats(user_id)


async def get_leaderboard(limit: int = 10) -> list[dict[str, Any]]:
    """便捷函数：获取排行榜

    Args:
        limit: 限制数量

    Returns:
        排行榜
    """
    return await ugc_incentive_service.get_leaderboard(limit)
