"""Points service v2 with enhanced features."""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from dataclasses import dataclass, field
from app.services.points.points_service_base import PointsServiceBase, PointsAction, PointsAccount, PointsTransaction, PointsRule, POINTS_RULES

logger = logging.getLogger(__name__)


class PointsRuleManager:
    def __init__(self):
        self._rules: dict[str, dict] = {}
        self._custom_rules: dict[str, dict] = {}
        for action, rule in POINTS_RULES.items():
            self._rules[action.value] = {
                "action": action.value,
                "points": rule.points,
                "max_daily": rule.max_daily,
                "description": rule.description,
                "is_custom": False,
            }

    def add_custom_rule(self, action: str, points: int, max_daily: int = 1, description: str = "", vip_multiplier: float = 1.0, requires_auth: bool = False) -> bool:
        if action in self._rules and not self._rules[action].get("is_custom"):
            logger.warning(f"Overwriting built-in rule: {action}")
        rule = {
            "action": action,
            "points": points,
            "max_daily": max_daily,
            "description": description,
            "is_custom": True,
            "vip_multiplier": vip_multiplier,
            "requires_auth": requires_auth,
        }
        self._rules[action] = rule
        self._custom_rules[action] = rule
        return True

    def remove_custom_rule(self, action: str) -> bool:
        rule = self._custom_rules.get(action)
        if rule:
            del self._custom_rules[action]
            if action in self._rules and self._rules[action].get("is_custom"):
                del self._rules[action]
            return True
        return False

    def get_rule(self, action: str) -> Optional[dict]:
        return self._rules.get(action)

    def get_all_rules(self) -> list[dict]:
        return list(self._rules.values())

    def validate_rule(self, action: str, amount: int) -> tuple[bool, str]:
        rule = self._rules.get(action)
        if rule is None:
            return False, f"未知的积分动作: {action}"
        if amount <= 0:
            return False, "积分必须大于 0"
        if amount > rule["max_daily"]:
            return False, f"超过每日上限 {rule['max_daily']}"
        return True, ""


class PointsChainValidator:
    def __init__(self):
        self._chain_configs: dict[str, dict] = {}
        self._chain_results: dict[str, dict] = {}

    def add_chain_config(self, chain_name: str, actions: list[str] = None, required_actions: list[str] = None, bonus_points: int = 0) -> None:
        self._chain_configs[chain_name] = {
            "chain_name": chain_name,
            "actions": actions or [],
            "required_actions": required_actions or [],
            "bonus_points": bonus_points,
        }

    def add_check(self, name: str, check_func=None) -> None:
        pass

    def validate(self, user_id: int, action: PointsAction, amount: int) -> dict:
        return {"valid": True, "checks_passed": 0}

    def validate_chain(self, user_id: int, chain_name: str, completed_actions: list[str]) -> dict:
        config = self._chain_configs.get(chain_name)
        if config is None:
            return {"valid": False, "error": f"未知的链路: {chain_name}"}
        required = config["required_actions"]
        missing = [a for a in required if a not in completed_actions]
        completed_required = [a for a in required if a in completed_actions]
        if missing:
            progress = f"{len(completed_required)}/{len(required)}"
            return {"valid": False, "missing": missing, "progress": progress}
        bonus = config["bonus_points"]
        message = f"恭喜完成 {chain_name}"
        return {"valid": True, "bonus_points": bonus, "message": message}

    def get_chain_status(self, user_id: int, chain_name: str) -> dict:
        config = self._chain_configs.get(chain_name)
        if config is None:
            return {"error": f"未知的链路: {chain_name}"}
        return {
            "chain_name": chain_name,
            "required_actions": config["required_actions"],
            "bonus_points": config["bonus_points"],
        }

    def get_checks(self) -> list[dict]:
        return []


class PointsAnalytics:
    def __init__(self):
        self._stats: dict[str, Any] = {
            "total_earned": {},
            "total_spent": {},
            "action_counts": {},
        }

    async def record_earn(self, user_id: int, action: str, amount: int) -> None:
        self._stats["action_counts"][action] = self._stats["action_counts"].get(action, 0) + 1
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._stats["total_earned"][date] = self._stats["total_earned"].get(date, 0) + amount

    async def record_spend(self, user_id: int, amount: int) -> None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._stats["total_spent"][date] = self._stats["total_spent"].get(date, 0) + amount

    def get_daily_stats(self, days: int = 7) -> dict:
        total_earned = sum(self._stats["total_earned"].values())
        total_spent = sum(self._stats["total_spent"].values())
        daily_data = []
        for i in range(days, -1, -1):
            date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
            earned = self._stats["total_earned"].get(date, 0)
            spent = self._stats["total_spent"].get(date, 0)
            daily_data.append({"date": date, "earned": earned, "spent": spent, "net": earned - spent})
        return {
            "period_days": days,
            "total_earned": total_earned,
            "total_spent": total_spent,
            "daily_data": daily_data,
        }

    def get_action_stats(self) -> dict:
        sorted_actions = sorted(self._stats["action_counts"].items(), key=lambda x: x[1], reverse=True)
        return {
            "total_actions": sum(self._stats["action_counts"].values()),
            "action_counts": dict(sorted_actions),
        }

    def record_action(self, user_id: int, action: PointsAction, amount: int) -> None:
        action_key = action.value
        self._stats["action_counts"][action_key] = self._stats["action_counts"].get(action_key, 0) + 1

    def get_user_analytics(self, user_id: int) -> dict:
        return {"total_actions": 0, "total_points": 0, "actions": {}}

    def get_global_stats(self) -> dict:
        return {"total_users": 0, "total_actions": 0}


class EnhancedPointsService:
    def __init__(self):
        self._base_service = PointsServiceBase()
        self.rule_manager = PointsRuleManager()
        self.chain_validator = PointsChainValidator()
        self.analytics = PointsAnalytics()
        self._daily_counts: dict[int, dict[str, int]] = {}

    def add_rule(self, action: PointsAction, points: int, daily_limit: Optional[int] = None, description: str = "") -> PointsRule:
        rule = PointsRule(action=action, points=points, max_daily=daily_limit or 1, description=description)
        return rule

    def get_rules(self) -> list[PointsRule]:
        return list(POINTS_RULES.values())

    async def award_points(self, user_id: int, action: str, description: Optional[str] = None, metadata: Optional[dict] = None) -> dict:
        try:
            points, error = await self._base_service_award(user_id, action, description)
        except Exception as e:
            return {"success": False, "points": 0, "error": str(e)}
        if error:
            return {"success": False, "points": 0, "error": error}
        await self.analytics.record_earn(user_id, action, points)
        return {"success": True, "points": points, "error": None}

    async def _base_service_award(self, user_id: int, action: str, description: Optional[str] = None) -> tuple[int, Optional[str]]:
        if hasattr(self._base_service, 'award_points') and callable(self._base_service.award_points):
            result = self._base_service.award_points(user_id, action, description=description)
            if hasattr(result, '__await__'):
                result = await result
            if isinstance(result, tuple) and len(result) == 2:
                return result
            return 0, None
        return 0, "No base service"

    async def redeem_points(self, user_id: int, points: int, product_id: Optional[str] = None, description: Optional[str] = None) -> dict:
        try:
            success, error = await self._base_service_redeem(user_id, points, product_id, description)
        except Exception as e:
            return {"success": False, "error": str(e)}
        if not success:
            return {"success": False, "error": error}
        await self.analytics.record_spend(user_id, points)
        return {"success": True, "error": None}

    async def _base_service_redeem(self, user_id: int, points: int, product_id: Optional[str] = None, description: Optional[str] = None) -> tuple[bool, Optional[str]]:
        if hasattr(self._base_service, 'redeem_points') and callable(self._base_service.redeem_points):
            result = self._base_service.redeem_points(user_id, points, product_id=product_id, description=description)
            if hasattr(result, '__await__'):
                result = await result
            if isinstance(result, tuple) and len(result) == 2:
                return result
            return False, None
        return False, "No base service"

    def get_balance(self, user_id: int) -> dict:
        if hasattr(self._base_service, 'get_balance') and callable(self._base_service.get_balance):
            balance = self._base_service.get_balance(user_id)
        else:
            balance = 0
        continuous_days = 0
        if hasattr(self._base_service, 'get_continuous_days') and callable(self._base_service.get_continuous_days):
            continuous_days = self._base_service.get_continuous_days(user_id)
        return {"user_id": user_id, "balance": balance, "continuous_days": continuous_days}

    def get_analytics(self, days: int = 7) -> dict:
        return {
            "daily_stats": self.analytics.get_daily_stats(days),
            "action_stats": self.analytics.get_action_stats(),
        }

    def reset_daily_counts(self) -> None:
        self._daily_counts.clear()


class PointsServiceV2(EnhancedPointsService):
    def __init__(self):
        super().__init__()
        self._v2_features: dict[str, Any] = {}

    def get_v2_features(self) -> dict:
        return dict(self._v2_features)

    def set_v2_feature(self, key: str, value: Any) -> None:
        self._v2_features[key] = value


enhanced_points_service = EnhancedPointsService()
points_service_v2 = PointsServiceV2()


async def award_points_v2(user_id: int, action: str, description: Optional[str] = None, metadata: Optional[dict] = None) -> dict:
    return await enhanced_points_service.award_points(user_id=user_id, action=action, description=description, metadata=metadata)


async def redeem_points_v2(user_id: int, points: int, product_id: Optional[str] = None, description: Optional[str] = None) -> dict:
    return await enhanced_points_service.redeem_points(user_id=user_id, points=points, product_id=product_id, description=description)


def get_points_balance_v2(user_id: int) -> dict:
    return enhanced_points_service.get_balance(user_id)


def get_points_rules_v2() -> list[dict]:
    return enhanced_points_service.rule_manager.get_all_rules()


def get_points_analytics_v2(days: int = 7) -> dict:
    return enhanced_points_service.get_analytics(days)
