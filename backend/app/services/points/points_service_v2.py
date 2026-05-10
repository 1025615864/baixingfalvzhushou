"""Points service v2 with enhanced features."""
from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass, field
from app.services.points.points_service_base import PointsServiceBase, PointsAction, PointsAccount, PointsTransaction, PointsRule, POINTS_RULES


class PointsRuleManager:
    def __init__(self):
        self._rules: dict[str, dict] = {}
        for action, rule in POINTS_RULES.items():
            self._rules[action.value] = {
                "action": action.value,
                "points": rule.points,
                "max_daily": rule.max_daily,
                "description": rule.description,
                "is_custom": False,
            }

    def add_custom_rule(self, action: str, points: int, description: str = "") -> bool:
        self._rules[action] = {
            "action": action,
            "points": points,
            "max_daily": 1,
            "description": description,
            "is_custom": True,
        }
        return True

    def remove_custom_rule(self, action: str) -> bool:
        rule = self._rules.get(action)
        if rule and rule.get("is_custom"):
            del self._rules[action]
            return True
        return False

    def get_rule(self, action: str) -> Optional[dict]:
        return self._rules.get(action)

    def get_all_rules(self) -> list[dict]:
        return list(self._rules.values())


class PointsChainValidator:
    def __init__(self):
        self._chain: list[dict] = []

    def add_check(self, name: str, check_func=None) -> None:
        self._chain.append({"name": name, "func": check_func})

    def validate(self, user_id: int, action: PointsAction, amount: int) -> dict:
        return {"valid": True, "checks_passed": len(self._chain)}

    def get_checks(self) -> list[dict]:
        return list(self._chain)


class PointsAnalytics:
    def __init__(self):
        self._data: dict[int, dict] = {}

    def record_action(self, user_id: int, action: PointsAction, amount: int) -> None:
        if user_id not in self._data:
            self._data[user_id] = {"total_actions": 0, "total_points": 0, "actions": {}}
        self._data[user_id]["total_actions"] += 1
        self._data[user_id]["total_points"] += amount
        action_key = action.value
        if action_key not in self._data[user_id]["actions"]:
            self._data[user_id]["actions"][action_key] = {"count": 0, "points": 0}
        self._data[user_id]["actions"][action_key]["count"] += 1
        self._data[user_id]["actions"][action_key]["points"] += amount

    def get_user_analytics(self, user_id: int) -> dict:
        return self._data.get(user_id, {"total_actions": 0, "total_points": 0, "actions": {}})

    def get_global_stats(self) -> dict:
        total_users = len(self._data)
        total_actions = sum(d["total_actions"] for d in self._data.values())
        return {"total_users": total_users, "total_actions": total_actions}


class EnhancedPointsService(PointsServiceBase):
    def __init__(self):
        super().__init__()
        self._rule_manager = PointsRuleManager()
        self._chain_validator = PointsChainValidator()
        self._analytics = PointsAnalytics()
        self._daily_counts: dict[int, dict[str, int]] = {}

    def add_rule(self, action: PointsAction, points: int, daily_limit: Optional[int] = None, description: str = "") -> PointsRule:
        rule = PointsRule(action=action, points=points, max_daily=daily_limit or 1, description=description)
        return rule

    def get_rules(self) -> list[PointsRule]:
        return list(POINTS_RULES.values())

    def add_points(self, user_id: int, action: PointsAction, amount: Optional[int] = None, description: Optional[str] = None) -> PointsTransaction:
        rule = POINTS_RULES.get(action)
        if rule and rule.max_daily:
            user_daily = self._daily_counts.setdefault(user_id, {})
            count = user_daily.get(action.value, 0)
            if count >= rule.max_daily:
                raise ValueError(f"今日{action.value}次数已达上限")
            user_daily[action.value] = count + 1
        pts = amount if amount is not None else (rule.points if rule else 0)
        txn = super().add_points(user_id, action, pts, description)
        self._analytics.record_action(user_id, action, pts)
        return txn

    def reset_daily_counts(self) -> None:
        self._daily_counts.clear()

    def get_analytics(self, user_id: int) -> dict:
        return self._analytics.get_user_analytics(user_id)


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


async def award_points_v2(user_id: int, action: PointsAction, amount: Optional[int] = None, description: Optional[str] = None) -> PointsTransaction:
    return enhanced_points_service.add_points(user_id, action, amount, description)


async def redeem_points_v2(user_id: int, amount: int, description: Optional[str] = None) -> PointsTransaction:
    return enhanced_points_service.deduct_points(user_id, amount, description)


async def get_points_balance_v2(user_id: int) -> int:
    return enhanced_points_service.get_balance(user_id)


async def get_points_rules_v2() -> list[dict]:
    return enhanced_points_service._rule_manager.get_all_rules()


async def get_points_analytics_v2(user_id: int) -> dict:
    return enhanced_points_service.get_analytics(user_id)
