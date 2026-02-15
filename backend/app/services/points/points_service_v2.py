"""积分体系 2.0 增强服务

提供积分规则配置、核心链路验证等功能。
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from ...services.points.points_service import (
    PointsRule,
    POINTS_RULES,
    get_points_service,
)

logger = logging.getLogger(__name__)


class PointsRuleManager:
    """积分规则管理器"""

    def __init__(self):
        self._rules: dict[str, PointsRule] = dict(POINTS_RULES)
        self._custom_rules: dict[str, dict[str, Any]] = {}

    def add_custom_rule(
        self,
        action: str,
        points: int,
        max_daily: int = 1,
        description: str = "",
        vip_multiplier: float = 1.0,
        requires_auth: bool = False,
    ) -> bool:
        """添加自定义积分规则

        Args:
            action: 动作名称
            points: 积分
            max_daily: 每日上限
            description: 描述
            vip_multiplier: VIP 加成
            requires_auth: 是否需要登录

        Returns:
            是否添加成功
        """
        if action in self._rules:
            logger.warning(f"Rule {action} already exists, updating...")
        else:
            logger.info(f"Adding new rule: {action}")

        self._custom_rules[action] = {
            "points": points,
            "max_daily": max_daily,
            "description": description,
            "vip_multiplier": vip_multiplier,
            "requires_auth": requires_auth,
        }

        return True

    def remove_custom_rule(self, action: str) -> bool:
        """移除自定义积分规则

        Args:
            action: 动作名称

        Returns:
            是否移除成功
        """
        if action in self._custom_rules:
            del self._custom_rules[action]
            logger.info(f"Removed custom rule: {action}")
            return True
        return False

    def get_all_rules(self) -> list[dict[str, Any]]:
        """获取所有积分规则

        Returns:
            规则列表
        """
        rules: list[dict[str, Any]] = []
        for action, rule in self._rules.items():
            rules.append({
                "action": action,
                "points": rule.points,
                "max_daily": rule.max_daily,
                "description": rule.description,
                "vip_multiplier": rule.vip_multiplier,
                "requires_auth": rule.requires_auth,
                "is_custom": action in self._custom_rules,
            })
        return rules

    def get_rule(self, action: str) -> dict[str, Any] | None:
        """获取指定规则

        Args:
            action: 动作名称

        Returns:
            规则详情
        """
        # 先检查自定义规则
        if action in self._custom_rules:
            custom = self._custom_rules[action]
            return {
                "action": action,
                "points": custom["points"],
                "max_daily": custom["max_daily"],
                "description": custom["description"],
                "vip_multiplier": custom["vip_multiplier"],
                "requires_auth": custom["requires_auth"],
                "is_custom": True,
            }
        # 再检查内置规则
        rule = self._rules.get(action)
        if rule:
            return {
                "action": action,
                "points": rule.points,
                "max_daily": rule.max_daily,
                "description": rule.description,
                "vip_multiplier": rule.vip_multiplier,
                "requires_auth": rule.requires_auth,
                "is_custom": False,
            }
        return None

    def validate_rule(self, action: str, points: int) -> tuple[bool, str]:
        """验证积分规则

        Args:
            action: 动作名称
            points: 积分

        Returns:
            (是否有效, 错误信息)
        """
        # 先检查自定义规则
        if action in self._custom_rules:
            custom = self._custom_rules[action]
            max_daily = custom["max_daily"]
            if points > max_daily:
                return False, f"积分超过每日上限 {max_daily}"
            if points <= 0:
                return False, "积分必须大于 0"
            return True, ""
        # 再检查内置规则
        rule = self._rules.get(action)
        if not rule:
            return False, f"未知的积分动作: {action}"

        if points > rule.max_daily:
            return False, f"积分超过每日上限 {rule.max_daily}"

        if points <= 0:
            return False, "积分必须大于 0"

        return True, ""


class PointsChainValidator:
    """积分核心链路验证器"""

    def __init__(self):
        self._chain_configs: dict[str, dict[str, Any]] = {}
        self._chain_results: dict[str, dict[str, Any]] = {}

    def add_chain_config(
        self,
        chain_name: str,
        actions: list[str],
        required_actions: list[str],
        bonus_points: int = 0,
    ) -> None:
        """配置积分链路

        Args:
            chain_name: 链路名称
            actions: 动作列表
            required_actions: 必需动作
            bonus_points: 额外奖励积分
        """
        self._chain_configs[chain_name] = {
            "actions": actions,
            "required_actions": required_actions,
            "bonus_points": bonus_points,
        }

    def validate_chain(
        self,
        user_id: int,
        chain_name: str,
        completed_actions: list[str],
    ) -> dict[str, Any]:
        """验证积分链路

        Args:
            user_id: 用户ID
            chain_name: 链路名称
            completed_actions: 已完成的动作

        Returns:
            验证结果
        """
        config = self._chain_configs.get(chain_name)
        if not config:
            return {
                "valid": False,
                "error": f"未知的链路: {chain_name}",
            }

        required = set(config["required_actions"])
        completed = set(completed_actions)

        missing = required - completed
        if missing:
            return {
                "valid": False,
                "completed": list(completed_actions),
                "missing": list(missing),
                "progress": f"{len(completed)}/{len(required)}",
                "bonus_points": 0,
            }

        bonus = config["bonus_points"]
        if bonus > 0:
            return {
                "valid": True,
                "completed": list(completed_actions),
                "progress": "100%",
                "bonus_points": bonus,
                "message": f"恭喜完成 {chain_name}，获得 {bonus} 额外积分！",
            }

        return {
            "valid": True,
            "completed": list(completed_actions),
            "progress": "100%",
            "bonus_points": 0,
            "message": f"恭喜完成 {chain_name}！",
        }

    def get_chain_status(self, user_id: int,
                         chain_name: str) -> dict[str, Any]:
        """获取链路状态

        Args:
            user_id: 用户ID
            chain_name: 链路名称

        Returns:
            链路状态
        """
        config = self._chain_configs.get(chain_name)
        if not config:
            return {"error": f"未知的链路: {chain_name}"}

        return {
            "chain_name": chain_name,
            "required_actions": config["required_actions"],
            "bonus_points": config["bonus_points"],
        }


class PointsAnalytics:
    """积分数据分析"""

    def __init__(self):
        self._stats: dict[str, dict[str, int]] = {
            "total_earned": {},
            "total_spent": {},
            "action_counts": {},
        }

    async def record_earn(self, user_id: int, action: str,
                          points: int) -> None:
        """记录积分获取

        Args:
            user_id: 用户ID
            action: 动作
            points: 积分
        """
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if date not in self._stats["total_earned"]:
            self._stats["total_earned"][date] = 0
        self._stats["total_earned"][date] += points

        if action not in self._stats["action_counts"]:
            self._stats["action_counts"][action] = 0
        self._stats["action_counts"][action] += 1

    async def record_spend(self, user_id: int, points: int) -> None:
        """记录积分消耗

        Args:
            user_id: 用户ID
            points: 积分
        """
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if date not in self._stats["total_spent"]:
            self._stats["total_spent"][date] = 0
        self._stats["total_spent"][date] += points

    def get_daily_stats(self, days: int = 7) -> dict[str, Any]:
        """获取每日统计

        Args:
            days: 天数

        Returns:
            统计信息
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        daily_data: list[dict[str, Any]] = []
        current = start_date
        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            earned = self._stats["total_earned"].get(date_str, 0)
            spent = self._stats["total_spent"].get(date_str, 0)
            daily_data.append({
                "date": date_str,
                "earned": earned,
                "spent": spent,
                "net": earned - spent,
            })
            current += timedelta(days=1)

        return {
            "period_days": days,
            "daily_data": daily_data,
            "total_earned": sum(self._stats["total_earned"].values()),
            "total_spent": sum(self._stats["total_spent"].values()),
        }

    def get_action_stats(self) -> dict[str, Any]:
        """获取动作统计

        Returns:
            统计信息
        """
        sorted_actions = sorted(
            self._stats["action_counts"].items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return {
            "action_counts": dict(sorted_actions),
            "total_actions": sum(self._stats["action_counts"].values()),
        }


class EnhancedPointsService:
    """增强积分服务"""

    def __init__(self):
        self.rule_manager = PointsRuleManager()
        self.chain_validator = PointsChainValidator()
        self.analytics = PointsAnalytics()
        self._base_service = get_points_service()

    async def award_points(
        self,
        user_id: int,
        action: str,
        description: str | None = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """奖励积分

        Args:
            user_id: 用户ID
            action: 动作
            description: 描述
            metadata: 元数据

        Returns:
            操作结果
        """
        points, error = await self._base_service.award_points(
            user_id=user_id,
            action=action,
            description=description,
            metadata=metadata,
        )

        if error:
            return {
                "success": False,
                "error": error,
                "points": 0,
            }

        await self.analytics.record_earn(user_id, action, points)

        return {
            "success": True,
            "points": points,
            "error": None,
        }

    async def redeem_points(
        self,
        user_id: int,
        points: int,
        product_id: str,
        description: str,
    ) -> dict[str, Any]:
        """消耗积分

        Args:
            user_id: 用户ID
            points: 积分
            product_id: 商品ID
            description: 描述

        Returns:
            操作结果
        """
        success, error = await self._base_service.redeem_points(
            user_id=user_id,
            points=points,
            product_id=product_id,
            description=description,
        )

        if success:
            await self.analytics.record_spend(user_id, points)

        return {
            "success": success,
            "error": error,
        }

    def get_balance(self, user_id: int) -> dict[str, Any]:
        """获取积分余额

        Args:
            user_id: 用户ID

        Returns:
            余额信息
        """
        balance = self._base_service.get_balance(user_id)
        return {
            "user_id": user_id,
            "balance": balance,
            "continuous_days": self._base_service.get_continuous_days(user_id),
        }

    def get_rules(self) -> list[dict[str, Any]]:
        """获取积分规则

        Returns:
            规则列表
        """
        return self.rule_manager.get_all_rules()

    def get_analytics(self, days: int = 7) -> dict[str, Any]:
        """获取分析数据

        Args:
            days: 天数

        Returns:
            分析数据
        """
        return {
            "daily_stats": self.analytics.get_daily_stats(days),
            "action_stats": self.analytics.get_action_stats(),
        }


# 单例实例
enhanced_points_service = EnhancedPointsService()


async def award_points_v2(
    user_id: int,
    action: str,
    description: str | None = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> dict[str, Any]:
    """便捷函数：奖励积分 V2

    Args:
        user_id: 用户ID
        action: 动作
        description: 描述
        metadata: 元数据

    Returns:
        操作结果
    """
    return await enhanced_points_service.award_points(
        user_id=user_id,
        action=action,
        description=description,
        metadata=metadata,
    )


async def redeem_points_v2(
    user_id: int,
    points: int,
    product_id: str,
    description: str,
) -> dict[str, Any]:
    """便捷函数：消耗积分 V2

    Args:
        user_id: 用户ID
        points: 积分
        product_id: 商品ID
        description: 描述

    Returns:
        操作结果
    """
    return await enhanced_points_service.redeem_points(
        user_id=user_id,
        points=points,
        product_id=product_id,
        description=description,
    )


def get_points_balance_v2(user_id: int) -> dict[str, Any]:
    """便捷函数：获取积分余额 V2

    Args:
        user_id: 用户ID

    Returns:
        余额信息
    """
    return enhanced_points_service.get_balance(user_id)


def get_points_rules_v2() -> list[dict[str, Any]]:
    """便捷函数：获取积分规则 V2

    Returns:
        规则列表
    """
    return enhanced_points_service.get_rules()


def get_points_analytics_v2(days: int = 7) -> dict[str, Any]:
    """便捷函数：获取积分分析 V2

    Args:
        days: 天数

    Returns:
        分析数据
    """
    return enhanced_points_service.get_analytics(days)
