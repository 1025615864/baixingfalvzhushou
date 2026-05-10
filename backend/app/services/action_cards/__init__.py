"""Action cards service."""
from __future__ import annotations
from typing import Optional


class ActionCardConfig:
    def __init__(self):
        self._cards: dict[str, dict] = {}
        self._next_id = 1

    def register_card(self, card_id: str, name: str, description: str, trigger_keywords: list[str], action_type: str, priority: int = 0) -> dict:
        self._cards[card_id] = {
            "id": card_id, "name": name, "description": description,
            "trigger_keywords": trigger_keywords, "action_type": action_type,
            "priority": priority, "enabled": True,
        }
        return {"id": card_id, "name": name, "registered": True}

    def get_card(self, card_id: str) -> dict:
        return self._cards.get(card_id, {})

    def list_cards(self) -> list[dict]:
        return list(self._cards.values())


class ActionCardTrigger:
    def __init__(self):
        self._config = ActionCardConfig()

    def detect_triggers(self, message: str, context: Optional[dict] = None) -> list[dict]:
        results = []
        message_lower = message.lower()
        for card in self._config.list_cards():
            if not card.get("enabled", True):
                continue
            for kw in card.get("trigger_keywords", []):
                if kw.lower() in message_lower:
                    results.append({
                        "card_id": card["id"], "card_name": card["name"],
                        "trigger_keyword": kw, "priority": card.get("priority", 0),
                    })
                    break
        results.sort(key=lambda x: x["priority"], reverse=True)
        return results[:5]


class ActionCardExecutor:
    def __init__(self):
        self._trigger = ActionCardTrigger()
        self._executions: dict[str, dict] = {}
        self._next_exec_id = 1

    def execute_card(self, card_id: str, user_id: int, session_id: str, params: Optional[dict] = None) -> dict:
        card = self._trigger._config.get_card(card_id)
        if not card:
            return {"success": False, "error": "卡片不存在"}
        exec_id = f"exec_{self._next_exec_id}_{user_id}"
        self._next_exec_id += 1
        action_result = {}
        at = card.get("action_type", "info")
        if at == "generate_document":
            action_result = {"document_id": f"doc_{exec_id}", "status": "generated"}
        elif at == "recommend_lawyer":
            action_result = {"lawyer_id": f"lawyer_{exec_id}", "status": "recommended"}
        elif at == "create_reminder":
            action_result = {"reminder_id": f"rem_{exec_id}", "status": "created"}
        self._executions[exec_id] = {"card_id": card_id, "user_id": user_id, "params": params or {}}
        return {"success": True, "card_id": card_id, "action_type": at, "execution_id": exec_id, "action_result": action_result}

    def get_user_executions(self, user_id: int) -> list[dict]:
        return [e for e in self._executions.values() if e["user_id"] == user_id]


class ActionCardService:
    def __init__(self):
        self._config = ActionCardConfig()
        self._trigger = ActionCardTrigger()
        self._executor = ActionCardExecutor()

    def register_default_cards(self) -> list[dict]:
        defaults = [
            ("generate_contract", "生成合同", "生成合同文档", ["合同", "协议"], "generate_document", 10),
            ("recommend_lawyer", "推荐律师", "推荐专业律师", ["律师", "咨询"], "recommend_lawyer", 9),
            ("create_reminder", "创建提醒", "创建法律提醒", ["提醒", "到期"], "create_reminder", 8),
            ("calculate_fee", "费用计算", "计算法律费用", ["费用", "收费"], "info", 7),
        ]
        results = []
        for cid, name, desc, kws, at, pri in defaults:
            results.append(self._config.register_card(cid, name, desc, kws, at, pri))
        return results

    async def detect_and_execute(self, message: str, user_id: int, session_id: str, context: Optional[dict] = None) -> dict:
        triggers = self._trigger.detect_triggers(message, context)
        if not triggers:
            return {"detected": False, "message": "未检测到可执行的动作"}
        executions = []
        for t in triggers[:2]:
            result = self._executor.execute_card(t["card_id"], user_id, session_id)
            executions.append(result)
        return {"detected": True, "triggered_count": len(triggers), "executions": executions}

    async def get_cards(self) -> list[dict]:
        return self._config.list_cards()

    async def get_user_history(self, user_id: int) -> list[dict]:
        return self._executor.get_user_executions(user_id)


action_card_service = ActionCardService()


async def detect_action_cards(message: str, user_id: int, session_id: str, context: Optional[dict] = None) -> dict:
    return await action_card_service.detect_and_execute(message, user_id, session_id, context)
