"""AI助手服务模块"""
from __future__ import annotations

from .models import AIModelConfig
from .knowledge_base import LegalKnowledgeBase
from .core import AICore
from .session import SessionManager
from .assistant import AILegalAssistant, ai_assistant, get_ai_assistant
from .chat import AIChatMixin
from .prompts import LegalAssistantPrompts

_ai_assistant: AILegalAssistant | None = None


def get_ai_assistant() -> AILegalAssistant:
    """获取AI助手实例（懒加载）"""
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AILegalAssistant()
    return _ai_assistant


__all__ = [
    "AIModelConfig",
    "LegalKnowledgeBase",
    "AICore",
    "SessionManager",
    "AILegalAssistant",
    "AIChatMixin",
    "get_ai_assistant",
    "ai_assistant",
    "LegalAssistantPrompts",
]
