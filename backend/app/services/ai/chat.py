"""AI聊天接口（兼容包装）"""
from .assistant import AILegalAssistant


class AIChatMixin(AILegalAssistant):
    """兼容旧的 AIChatMixin 接口，保留 AILegalAssistant 能力。"""

    pass
