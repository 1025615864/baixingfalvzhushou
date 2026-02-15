"""系统管理路由模块

包含：AI配置、系统配置、密钥管理、操作日志、数据统计、FAQ自动生成、监控指标等功能。
"""

from fastapi import APIRouter

from .ai_config import router as ai_config_router
from .config import router as config_router
from .secrets import router as secrets_router
from .logs import router as logs_router
from .analytics import router as analytics_router
from .faq import router as faq_router
from .voice import router as voice_router
from .metrics import router as metrics_router

router = APIRouter(prefix="/system", tags=["系统管理"])

# 挂载子路由
router.include_router(ai_config_router)
router.include_router(config_router)
router.include_router(secrets_router)
router.include_router(logs_router)
router.include_router(analytics_router)
router.include_router(faq_router)
router.include_router(voice_router)
router.include_router(metrics_router)

__all__ = ["router"]
