"""AI助手API路由

此模块已重构为子模块结构：
- ai/chat.py: 聊天相关端点
- ai/consultations.py: 咨询管理端点
- ai/share.py: 分享功能端点
- ai/transcription.py: 语音转写端点
- ai/analysis.py: 文件分析端点

此文件保留为向后兼容的聚合层。
"""
import sys
import logging

from fastapi import APIRouter

from .ai.chat import router as chat_router
from .ai.consultations import router as consultations_router
from .ai.share import router as share_router
from .ai.transcription import router as transcription_router
from .ai.analysis import router as analysis_router

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI法律助手"])

# 聚合所有子模块路由
router.include_router(chat_router)
router.include_router(consultations_router)
router.include_router(share_router)
router.include_router(transcription_router)
router.include_router(analysis_router)

# 导出settings供测试使用 - 引用chat模块中的settings对象
# 这样可以保持单例模式，同时让测试可以访问
_chat_module = sys.modules.get('app.routers.ai.chat')
if _chat_module is not None and hasattr(_chat_module, 'settings'):
    settings = _chat_module.settings
else:
    # 如果模块尚未加载，从配置重新获取
    from ...config import get_settings
    settings = get_settings()

__all__ = ["router", "settings"]
