"""积分体系服务 (兼容性封装)

提供积分规则配置、获取、消耗、查询功能。

此模块为兼容性层，实际实现已迁移到 points/ 目录。
建议使用 points_manager 模块或 points/ 目录中的服务。
"""
import logging
from datetime import datetime, timezone
from typing import Any

from app.services.points.points_service import (
    PointsAction,
    PointsRule,
    PointsHistoryItem,
    POINTS_RULES,
    get_points_service,
)
from app.services.points.points_service_db import (
    get_balance_db,
    award_points_db,
    redeem_points_db,
)
from app.services.points_manager import (
    get_points_manager,
    award_points,
    redeem_points,
    get_points_balance,
    daily_signin,
    get_points_rules,
    get_points_rule,
)

logger = logging.getLogger(__name__)


class PointsRuleConfig:
    """积分规则配置 - 已迁移至 points/"""

    def __init__(self):
        logger.warning(
            "PointsRuleConfig is deprecated, use points/ module instead"
        )
        self._earn_rules: dict[str, dict[str, Any]] = {}
        self._spend_rules: dict[str, dict[str, Any]] = {}

    def register_earn_rule(
        self,
        *,
        rule_id: str,
        action: str,
        points: int,
        description: str,
        daily_limit: int = 1,
        cooldown_seconds: int = 0,
    ) -> dict[str, Any]:
        self._earn_rules[rule_id] = {
            "rule_id": rule_id,
            "action": action,
            "points": points,
            "description": description,
            "daily_limit": daily_limit,
            "cooldown_seconds": cooldown_seconds,
            "enabled": True,
        }
        return {"registered": True, "rule_id": rule_id, "action": action}

    def register_spend_rule(
        self,
        *,
        rule_id: str,
        action: str,
        cost_points: int,
        description: str,
        min_points: int = 0,
    ) -> dict[str, Any]:
        self._spend_rules[rule_id] = {
            "rule_id": rule_id,
            "action": action,
            "cost_points": cost_points,
            "description": description,
            "min_points": min_points,
            "enabled": True,
        }
        return {"registered": True, "rule_id": rule_id, "action": action}

    def get_earn_rule(self, action: str):
        for rule in self._earn_rules.values():
            if rule.get("action") == action and rule.get("enabled", True):
                return rule
        return None

    def get_spend_rule(self, action: str):
        for rule in self._spend_rules.values():
            if rule.get("action") == action and rule.get("enabled", True):
                return rule
        return None

    def list_earn_rules(self):
        return [rule for rule in self._earn_rules.values() if rule.get("enabled", True)]

    def list_spend_rules(self):
        return [rule for rule in self._spend_rules.values() if rule.get("enabled", True)]


class PointsLedger:
    """积分账本 - 已迁移至数据库"""

    def __init__(self):
        logger.warning(
            "PointsLedger is deprecated, database storage is used now"
        )
        self._balances: dict[int, dict[str, int]] = {}
        self._transactions: dict[int, list[dict[str, Any]]] = {}

    def _ensure_user(self, user_id: int) -> None:
        if user_id not in self._balances:
            self._balances[user_id] = {
                "current_balance": 0,
                "total_earned": 0,
                "total_spent": 0,
            }
            self._transactions[user_id] = []

    def _record_transaction(
        self,
        *,
        user_id: int,
        points: int,
        action: str,
        description: str,
        balance_before: int,
        balance_after: int,
        tx_type: str,
    ) -> dict[str, Any]:
        tx_list = self._transactions[user_id]
        tx_id = f"tx_{user_id}_{len(tx_list) + 1}"
        tx = {
            "id": len(tx_list) + 1,
            "transaction_id": tx_id,
            "user_id": user_id,
            "action": action,
            "points": points,
            "type": tx_type,
            "description": description,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        tx_list.append(tx)
        return tx

    def get_balance(self, user_id: int) -> dict[str, Any]:
        info = self._balances.get(user_id)
        if not info:
            return {
                "user_id": user_id,
                "current_balance": 0,
                "total_earned": 0,
                "total_spent": 0,
            }
        return {
            "user_id": user_id,
            "current_balance": info["current_balance"],
            "total_earned": info["total_earned"],
            "total_spent": info["total_spent"],
        }

    def credit(self, user_id: int, points: int, action: str, description: str):
        self._ensure_user(user_id)
        balance_before = self._balances[user_id]["current_balance"]
        balance_after = balance_before + points
        self._balances[user_id]["current_balance"] = balance_after
        if points >= 0:
            self._balances[user_id]["total_earned"] += points
            tx_type = "credit"
        else:
            self._balances[user_id]["total_spent"] += abs(points)
            tx_type = "debit"
        tx = self._record_transaction(
            user_id=user_id,
            points=points,
            action=action,
            description=description,
            balance_before=balance_before,
            balance_after=balance_after,
            tx_type=tx_type,
        )
        return {
            "transaction_id": tx["transaction_id"],
            "user_id": user_id,
            "points": points,
            "new_balance": balance_after,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "action": action,
            "description": description,
        }

    def debit(self, user_id: int, points: int, action: str, description: str):
        if user_id not in self._balances:
            return {"error": "用户积分账户不存在"}
        balance_before = self._balances[user_id]["current_balance"]
        if points > 0 and balance_before < points:
            return {"error": "积分不足"}
        balance_after = balance_before - points
        self._balances[user_id]["current_balance"] = balance_after
        if points > 0:
            self._balances[user_id]["total_spent"] += points
            tx_type = "debit"
        else:
            self._balances[user_id]["total_earned"] += abs(points)
            tx_type = "credit"
        points_delta = -points
        tx = self._record_transaction(
            user_id=user_id,
            points=points_delta,
            action=action,
            description=description,
            balance_before=balance_before,
            balance_after=balance_after,
            tx_type=tx_type,
        )
        return {
            "transaction_id": tx["transaction_id"],
            "user_id": user_id,
            "points": points_delta,
            "new_balance": balance_after,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "action": action,
            "description": description,
        }

    def get_transactions(self, user_id: int, limit: int = 50):
        txs = self._transactions.get(user_id, [])
        if limit <= 0:
            return []
        return txs[-limit:]


class PointsService:
    """积分服务 - 已迁移至 points_manager"""

    def __init__(self):
        self._config = PointsRuleConfig()
        self._ledger = PointsLedger()
        logger.warning(
            "PointsService is deprecated, use get_points_manager() instead"
        )

    def register_default_rules(self) -> dict[str, Any]:
        earn_rules = [
            ("daily_signin", "daily_signin", 10, "每日签到"),
            ("consultation_complete", "consultation_complete", 10, "完成咨询"),
            ("document_generate", "document_generate", 20, "生成文书"),
            ("forum_post", "forum_post", 20, "发布帖子"),
            ("forum_comment", "forum_comment", 5, "发表评论"),
            ("invite_register", "invite_register", 50, "邀请注册"),
            ("share_content", "share_content", 10, "分享内容"),
        ]
        for rule_id, action, points, description in earn_rules:
            self._config.register_earn_rule(
                rule_id=rule_id,
                action=action,
                points=points,
                description=description,
            )

        spend_rules = [
            ("consultation_discount", "consultation_discount", 100, "咨询折扣", 0),
            ("vip_upgrade", "vip_upgrade", 500, "会员升级", 0),
            ("gift_exchange", "gift_exchange", 1000, "礼品兑换", 500),
            ("document_upgrade", "document_upgrade", 200, "文书升级", 0),
        ]
        for rule_id, action, cost_points, description, min_points in spend_rules:
            self._config.register_spend_rule(
                rule_id=rule_id,
                action=action,
                cost_points=cost_points,
                description=description,
                min_points=min_points,
            )

        return {
            "earn_rules_registered": len(earn_rules),
            "spend_rules_registered": len(spend_rules),
        }

    async def earn_points(self, user_id: int, action: str, description: str | None = None) -> dict[str, Any]:
        rule = self._config.get_earn_rule(action)
        if not rule:
            return {
                "success": False,
                "error": "未找到对应积分规则",
                "action": action,
            }
        desc = description or rule.get("description", "")
        result = self._ledger.credit(user_id, rule.get("points", 0), action, desc)
        return {
            "success": True,
            "points_earned": rule.get("points", 0),
            "new_balance": result.get("new_balance", 0),
            "action": action,
        }

    async def spend_points(self, user_id: int, action: str, description: str | None = None) -> dict[str, Any]:
        rule = self._config.get_spend_rule(action)
        if not rule:
            return {"success": False, "error": "未找到对应消耗规则"}
        balance_info = self._ledger.get_balance(user_id)
        balance = balance_info.get("current_balance", 0)
        required = rule.get("cost_points", 0)
        if balance < required:
            return {
                "success": False,
                "error": "积分不足",
                "current_balance": balance,
                "required": required,
                "action": action,
            }
        desc = description or rule.get("description", "")
        result = self._ledger.debit(user_id, required, action, desc)
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "current_balance": balance,
                "required": required,
                "action": action,
            }
        return {
            "success": True,
            "points_spent": required,
            "new_balance": result.get("new_balance", balance),
            "action": action,
        }

    async def get_balance(self, user_id: int) -> dict[str, Any]:
        return self._ledger.get_balance(user_id)

    async def get_transactions(self, user_id: int, limit: int = 50):
        return self._ledger.get_transactions(user_id, limit=limit)

    async def get_rules(self) -> dict[str, Any]:
        return {
            "earn_rules": self._config.list_earn_rules(),
            "spend_rules": self._config.list_spend_rules(),
        }


points_service = PointsService()


async def earn_points(user_id: int, action: str, description: str | None = None) -> dict[str, Any]:
    """便捷函数：获取积分 - 已弃用"""
    logger.warning("earn_points is deprecated, use award_points instead")
    return await points_service.earn_points(user_id, action, description=description)


async def spend_points(user_id: int, action: str, description: str | None = None) -> dict[str, Any]:
    """便捷函数：消耗积分 - 已弃用"""
    logger.warning("spend_points is deprecated, use redeem_points instead")
    return await points_service.spend_points(user_id, action, description=description)


async def get_points_balance(user_id: int) -> dict[str, Any]:
    """便捷函数：查询积分余额 - 已弃用"""
    logger.warning("get_points_balance is deprecated")
    return await points_service.get_balance(user_id)
