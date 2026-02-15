"""AI法律咨询助手服务

该模块已重构，核心组件已拆分到 ai/ 目录：
- from ..services.ai import AIModelConfig  # AI模型配置
- from ..services.ai import LegalKnowledgeBase  # 法律知识库
- from ..services.ai import AICore  # AI核心工具
- from ..services.ai import SessionManager  # 会话管理
- from ..services.ai import AILegalAssistant  # AI助手主类

向后兼容导入仍然可用。
"""

# 重新导出核心组件（向后兼容）
from ..services.ai import (
    AIModelConfig,
    LegalKnowledgeBase,
    AICore,
    SessionManager,
    AILegalAssistant,
)

# 保持原有文件的完整内容（包含聊天方法）
# 这样可以确保向后兼容，不需要修改任何调用方

_ai_assistant = None


def get_ai_assistant() -> AILegalAssistant:
    """获取AI助手实例（懒加载）"""
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AILegalAssistant()
    return _ai_assistant
