"""AI 行动卡服务

提供 AI 咨询中触发的行动卡片功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ActionCardConfig:
    """行动卡配置"""

    def __init__(self):
        self._cards: dict[str, dict[str, Any]] = {}

    def register_card(
        self,
        card_id: str,
        name: str,
        description: str,
        trigger_keywords: list[str],
        action_type: str,
        priority: int = 0,
    ) -> dict[str, Any]:
        """注册行动卡

        Args:
            card_id: 卡片ID
            name: 名称
            description: 描述
            trigger_keywords: 触发关键词
            action_type: 动作类型
            priority: 优先级

        Returns:
            配置结果
        """
        self._cards[card_id] = {
            "id": card_id,
            "name": name,
            "description": description,
            "trigger_keywords": trigger_keywords,
            "action_type": action_type,
            "priority": priority,
            "enabled": True,
        }

        return {
            "id": card_id,
            "name": name,
            "registered": True,
        }

    def get_card(self, card_id: str) -> dict[str, Any]:
        """获取卡片配置

        Args:
            card_id: 卡片ID

        Returns:
            卡片配置
        """
        return self._cards.get(card_id, {})

    def list_cards(self) -> list[dict[str, Any]]:
        """列出所有卡片

        Returns:
            卡片列表
        """
        return list(self._cards.values())


class ActionCardTrigger:
    """行动卡触发器"""

    def __init__(self):
        self._config = ActionCardConfig()
        self._history: list[dict[str, Any]] = []

    def detect_triggers(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """检测触发

        Args:
            message: 消息内容
            context: 上下文

        Returns:
            触发的卡片列表
        """
        triggered = []
        message_lower = message.lower()

        for card_id, card in self._config._cards.items():
            if not card.get("enabled", True):
                continue

            for keyword in card.get("trigger_keywords", []):
                if keyword.lower() in message_lower:
                    triggered.append({
                        "card_id": card_id,
                        "card_name": card["name"],
                        "action_type": card["action_type"],
                        "priority": card["priority"],
                        "trigger_keyword": keyword,
                    })
                    break

        triggered.sort(key=lambda x: x["priority"], reverse=True)

        return triggered[:5]


class ActionCardExecutor:
    """行动卡执行器"""

    def __init__(self):
        self._trigger = ActionCardTrigger()
        self._executions: dict[str, dict[str, Any]] = {}

    def execute_card(
        self,
        card_id: str,
        user_id: int,
        session_id: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """执行卡片

        Args:
            card_id: 卡片ID
            user_id: 用户ID
            session_id: 会话ID
            params: 参数

        Returns:
            执行结果
        """
        card = self._trigger._config.get_card(card_id)
        if not card:
            return {
                "card_id": card_id,
                "success": False,
                "error": "卡片不存在",
            }

        action_type = card.get("action_type", "info")
        execution_id = f"exec_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{user_id}"

        result = {
            "execution_id": execution_id,
            "card_id": card_id,
            "card_name": card["name"],
            "action_type": action_type,
            "user_id": user_id,
            "session_id": session_id,
            "params": params or {},
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

        if action_type == "generate_document":
            result["action_result"] = {
                "document_id": f"doc_{execution_id}",
                "status": "generated"}
        elif action_type == "recommend_lawyer":
            result["action_result"] = {
                "lawyer_id": None, "status": "recommended"}
        elif action_type == "create_reminder":
            result["action_result"] = {
                "reminder_id": f"rem_{execution_id}",
                "status": "created"}
        else:
            result["action_result"] = {"status": "completed"}

        self._executions[execution_id] = result

        logger.info(f"Executed action card: {card_id} for user {user_id}")

        return {
            "execution_id": execution_id,
            "card_id": card_id,
            "success": True,
            "action_type": action_type,
            "action_result": result.get("action_result"),
        }

    def get_user_executions(self, user_id: int) -> list[dict[str, Any]]:
        """获取用户执行记录

        Args:
            user_id: 用户ID

        Returns:
            执行记录列表
        """
        return [e for e in self._executions.values() if e.get("user_id")
                == user_id]


class ActionCardService:
    """行动卡服务"""

    def __init__(self):
        self._config = ActionCardConfig()
        self._trigger = ActionCardTrigger()
        self._executor = ActionCardExecutor()

    def register_default_cards(self) -> list[dict[str, Any]]:
        """注册默认卡片

        Returns:
            注册结果列表
        """
        default_cards = [
            {
                "card_id": "generate_contract",
                "name": "生成合同",
                "description": "根据对话内容生成合同文书",
                "trigger_keywords": ["合同", "协议", "起草", "拟定"],
                "action_type": "generate_document",
                "priority": 10,
            },
            {
                "card_id": "recommend_lawyer",
                "name": "推荐律师",
                "description": "推荐合适的律师",
                "trigger_keywords": ["律师", "咨询律师", "找律师", "聘请律师"],
                "action_type": "recommend_lawyer",
                "priority": 9,
            },
            {
                "card_id": "create_reminder",
                "name": "创建提醒",
                "description": "创建诉讼时效提醒",
                "trigger_keywords": ["提醒", "时效", "截止日期", "期限"],
                "action_type": "create_reminder",
                "priority": 8,
            },
            {
                "card_id": "calculate_fee",
                "name": "费用计算",
                "description": "计算诉讼费用",
                "trigger_keywords": ["费用", "诉讼费", "多少钱", "成本"],
                "action_type": "calculate_fee",
                "priority": 7,
            },
        ]

        results = []
        for card in default_cards:
            result = self._config.register_card(**card)
            results.append(result)

        return results

    async def detect_and_execute(
        self,
        message: str,
        user_id: int,
        session_id: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """检测并执行

        Args:
            message: 消息内容
            user_id: 用户ID
            session_id: 会话ID
            context: 上下文

        Returns:
            执行结果
        """
        triggered = self._trigger.detect_triggers(message, context)

        if not triggered:
            return {
                "detected": False,
                "message": "未检测到可执行的动作",
            }

        results = []
        for card in triggered[:2]:
            result = self._executor.execute_card(
                card_id=card["card_id"],
                user_id=user_id,
                session_id=session_id,
            )
            results.append(result)

        return {
            "detected": True,
            "triggered_count": len(results),
            "executions": results,
        }

    async def get_cards(self) -> list[dict[str, Any]]:
        """获取所有卡片

        Returns:
            卡片列表
        """
        return self._config.list_cards()

    async def get_user_history(self, user_id: int) -> list[dict[str, Any]]:
        """获取用户历史

        Args:
            user_id: 用户ID

        Returns:
            执行历史
        """
        return self._executor.get_user_executions(user_id)


# 单例实例
action_card_service = ActionCardService()


async def detect_action_cards(
    message: str,
    user_id: int,
    session_id: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """便捷函数：检测并执行行动卡

    Args:
        message: 消息内容
        user_id: 用户ID
        session_id: 会话ID
        context: 上下文

    Returns:
        执行结果
    """
    return await action_card_service.detect_and_execute(
        message=message,
        user_id=user_id,
        session_id=session_id,
        context=context,
    )
