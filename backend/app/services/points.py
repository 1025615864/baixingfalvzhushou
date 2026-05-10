"""Points service - standalone module for direct import."""
from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Optional, Any


class PointsRuleConfig:
    def __init__(self):
        self._earn_rules: dict[str, dict] = {}
        self._spend_rules: dict[str, dict] = {}

    def register_earn_rule(self, rule_id: str, action: str, points: int, description: str = "", daily_limit: int = 1, cooldown_seconds: int = 0) -> dict:
        self._earn_rules[rule_id] = {
            "rule_id": rule_id,
            "action": action,
            "points": points,
            "description": description,
            "daily_limit": daily_limit,
            "cooldown_seconds": cooldown_seconds,
            "enabled": True,
        }
        return {"registered": True, "rule_id": rule_id}

    def register_spend_rule(self, rule_id: str, action: str, cost_points: int, description: str = "", min_points: int = 0) -> dict:
        self._spend_rules[rule_id] = {
            "rule_id": rule_id,
            "action": action,
            "cost_points": cost_points,
            "description": description,
            "min_points": min_points,
            "enabled": True,
        }
        return {"registered": True, "rule_id": rule_id}

    def get_earn_rule(self, action: str) -> Optional[dict]:
        for rule in self._earn_rules.values():
            if rule["action"] == action and rule.get("enabled", True):
                return rule
        return None

    def get_spend_rule(self, action: str) -> Optional[dict]:
        for rule in self._spend_rules.values():
            if rule["action"] == action and rule.get("enabled", True):
                return rule
        return None

    def list_earn_rules(self) -> list[dict]:
        return [r for r in self._earn_rules.values() if r.get("enabled", True)]

    def list_spend_rules(self) -> list[dict]:
        return [r for r in self._spend_rules.values() if r.get("enabled", True)]


class PointsLedger:
    def __init__(self):
        self._balances: dict[int, dict] = {}
        self._transactions: dict[int, list[dict]] = {}
        self._tx_counter = 0

    def _next_tx_id(self, user_id: int) -> str:
        self._tx_counter += 1
        return f"tx_{self._tx_counter}_{user_id}"

    def get_balance(self, user_id: int) -> dict:
        bal = self._balances.get(user_id)
        if bal is None:
            return {"user_id": user_id, "current_balance": 0, "total_earned": 0, "total_spent": 0}
        return dict(bal)

    def credit(self, user_id: int, points: int, action: str, description: str = "") -> dict:
        if user_id not in self._balances:
            self._balances[user_id] = {"user_id": user_id, "current_balance": 0, "total_earned": 0, "total_spent": 0}
        bal = self._balances[user_id]
        before = bal["current_balance"]
        bal["current_balance"] += points
        if points > 0:
            bal["total_earned"] += points
        else:
            bal["total_spent"] += abs(points)
        after = bal["current_balance"]
        tx_id = self._next_tx_id(user_id)
        tx = {
            "id": tx_id,
            "user_id": user_id,
            "action": action,
            "points": points,
            "type": "credit" if points > 0 else "debit",
            "description": description,
            "balance_before": before,
            "balance_after": after,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if user_id not in self._transactions:
            self._transactions[user_id] = []
        self._transactions[user_id].append(tx)
        return {"transaction_id": tx_id, "user_id": user_id, "points": points, "new_balance": after}

    def debit(self, user_id: int, points: int, action: str, description: str = "") -> dict:
        if user_id not in self._balances:
            return {"error": "用户积分账户不存在"}
        bal = self._balances[user_id]
        if bal["current_balance"] < points:
            return {"error": "积分不足", "current_balance": bal["current_balance"], "required": points}
        before = bal["current_balance"]
        bal["current_balance"] -= points
        bal["total_spent"] += points
        after = bal["current_balance"]
        tx_id = self._next_tx_id(user_id)
        tx = {
            "id": tx_id,
            "user_id": user_id,
            "action": action,
            "points": -points,
            "type": "debit",
            "description": description,
            "balance_before": before,
            "balance_after": after,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if user_id not in self._transactions:
            self._transactions[user_id] = []
        self._transactions[user_id].append(tx)
        return {"transaction_id": tx_id, "user_id": user_id, "points": -points, "new_balance": after}

    def get_transactions(self, user_id: int, limit: int = 20) -> list[dict]:
        txs = self._transactions.get(user_id, [])
        return list(reversed(txs[-limit:]))


class PointsService:
    def __init__(self):
        self._rule_config = PointsRuleConfig()
        self._ledger = PointsLedger()

    def register_default_rules(self) -> dict:
        earn_rules = [
            ("daily_signin", "daily_signin", 10, "每日签到"),
            ("consultation_complete", "consultation_complete", 20, "完成咨询"),
            ("document_generate", "document_generate", 15, "生成文档"),
            ("forum_post", "forum_post", 5, "论坛发帖"),
            ("forum_comment", "forum_comment", 3, "论坛评论"),
            ("invite_register", "invite_register", 50, "邀请注册"),
            ("share_content", "share_content", 5, "分享内容"),
        ]
        spend_rules = [
            ("vip_upgrade", "vip_upgrade", 500, "VIP升级"),
            ("consultation_discount", "consultation_discount", 100, "咨询折扣"),
            ("document_download", "document_download", 30, "文档下载"),
            ("gift_exchange", "gift_exchange", 1000, "礼品兑换", 500),
        ]
        for r in earn_rules:
            self._rule_config.register_earn_rule(rule_id=r[0], action=r[1], points=r[2], description=r[3])
        for r in spend_rules:
            min_pts = r[4] if len(r) > 4 else 0
            self._rule_config.register_spend_rule(rule_id=r[0], action=r[1], cost_points=r[2], description=r[3], min_points=min_pts)
        return {"earn_rules_registered": len(earn_rules), "spend_rules_registered": len(spend_rules)}

    async def earn_points(self, user_id: int, action: str, description: Optional[str] = None) -> dict:
        rule = self._rule_config.get_earn_rule(action)
        if rule is None:
            return {"success": False, "error": "未找到对应积分规则", "action": action}
        desc = description or rule.get("description", "")
        result = self._ledger.credit(user_id, rule["points"], action, desc)
        return {
            "success": True,
            "points_earned": rule["points"],
            "new_balance": result["new_balance"],
            "action": action,
        }

    async def spend_points(self, user_id: int, action: str, description: Optional[str] = None) -> dict:
        rule = self._rule_config.get_spend_rule(action)
        if rule is None:
            return {"success": False, "error": "未找到对应消耗规则", "action": action}
        balance = self._ledger.get_balance(user_id)
        if balance["current_balance"] < rule["cost_points"]:
            return {"success": False, "error": "积分不足", "current_balance": balance["current_balance"], "required": rule["cost_points"]}
        if rule.get("min_points", 0) > 0 and balance["current_balance"] < rule["min_points"]:
            pass
        desc = description or rule.get("description", "")
        result = self._ledger.debit(user_id, rule["cost_points"], action, desc)
        if "error" in result:
            return {"success": False, "error": result["error"]}
        return {
            "success": True,
            "points_spent": rule["cost_points"],
            "new_balance": result["new_balance"],
            "action": action,
        }

    async def get_balance(self, user_id: int) -> dict:
        return self._ledger.get_balance(user_id)

    async def get_transactions(self, user_id: int, limit: int = 20) -> list[dict]:
        return self._ledger.get_transactions(user_id, limit=limit)

    async def get_rules(self) -> dict:
        return {
            "earn_rules": self._rule_config.list_earn_rules(),
            "spend_rules": self._rule_config.list_spend_rules(),
        }


points_service = PointsService()


async def earn_points(user_id: int, action: str, description: Optional[str] = None) -> dict:
    return await points_service.earn_points(user_id, action, description)


async def spend_points(user_id: int, action: str, description: Optional[str] = None) -> dict:
    return await points_service.spend_points(user_id, action, description)


async def get_points_balance(user_id: int) -> dict:
    return await points_service.get_balance(user_id)
