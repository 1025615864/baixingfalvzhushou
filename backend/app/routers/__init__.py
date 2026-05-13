"""API路由 - BFF 聚合层

⚠️ Backend 作为 BFF 层，不再直接包含业务逻辑。
⚠️ 业务逻辑已迁移到对应微服务，此处仅负责路由转发和数据聚合。
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

api_router = APIRouter()

# ==========================================
# 本地保留路由（BFF 职责范围内）— 注册在代理之前，确保优先匹配
# ==========================================

# 管理后台（本地管理功能）
try:
    from . import admin_v1
    api_router.include_router(admin_v1.router)
except ImportError:
    logger.warning("admin_v1路由未加载")

try:
    from . import admin
    api_router.include_router(admin.router)
except ImportError:
    logger.warning("admin路由未加载")

try:
    from . import admin_monitor
    api_router.include_router(admin_monitor.router)
except ImportError:
    logger.warning("admin_monitor路由未加载")

# 首页聚合（可能聚合多个微服务数据）
try:
    from . import home
    api_router.include_router(home.router)
except ImportError:
    logger.warning("home路由未加载")

# 文件上传（本地处理）
try:
    from . import upload
    api_router.include_router(upload.router)
except ImportError:
    logger.warning("upload路由未加载")

# 跨域处理
try:
    from . import cross_domain
    api_router.include_router(cross_domain.router)
except ImportError:
    logger.warning("cross_domain路由未加载")

# AB测试、埋点分析（本地BFF功能）
try:
    from . import ab_testing
    api_router.include_router(ab_testing.router)
except ImportError:
    logger.warning("ab_testing路由未加载")

# 安全相关（认证、授权网关）
try:
    from . import security
    api_router.include_router(security.router)
except ImportError:
    logger.warning("security路由未加载")

# 微信生态（扫码登录、消息推送）
try:
    from . import wechat
    api_router.include_router(wechat.router)
except ImportError:
    logger.warning("wechat路由未加载")

# WebSocket（实时通信基础设施）
try:
    from . import websocket
    api_router.include_router(websocket.router)
except ImportError:
    logger.warning("websocket路由未加载")

try:
    from . import news
    api_router.include_router(news.router)
except ImportError:
    logger.warning("news路由未加载")

try:
    from . import payment
    api_router.include_router(payment.router)
except ImportError:
    logger.warning("payment路由未加载")

try:
    from . import order
    api_router.include_router(order.router)
except ImportError:
    logger.warning("order路由未加载")

try:
    from . import search
    api_router.include_router(search.router)
except ImportError:
    logger.warning("search路由未加载")

try:
    from . import forum
    api_router.include_router(forum.router)
except ImportError:
    logger.warning("forum路由未加载")

try:
    from . import analytics
    api_router.include_router(analytics.router)
except ImportError:
    logger.warning("analytics路由未加载")

try:
    from . import vertical_channel
    api_router.include_router(vertical_channel.router)
except ImportError:
    logger.warning("vertical_channel路由未加载")

try:
    from . import enterprise
    api_router.include_router(enterprise.router)
except ImportError:
    logger.warning("enterprise路由未加载")

try:
    from . import settlement
    api_router.include_router(settlement.router)
except ImportError:
    logger.warning("settlement路由未加载")

try:
    from . import membership
    api_router.include_router(membership.router)
except ImportError:
    logger.warning("membership路由未加载")

try:
    from . import promotion
    api_router.include_router(promotion.router)
except ImportError:
    logger.warning("promotion路由未加载")

try:
    from . import feedback
    api_router.include_router(feedback.router)
except ImportError:
    logger.warning("feedback路由未加载")

try:
    from . import user_security
    api_router.include_router(user_security.router)
except ImportError:
    logger.warning("user_security路由未加载")

try:
    from . import system_config
    api_router.include_router(system_config.router)
except ImportError:
    logger.warning("system_config路由未加载")

# 律师相关
try:
    from . import lawyer
    api_router.include_router(lawyer.router)
    api_router.include_router(lawyer.lawfirm_router)
    api_router.include_router(lawyer.verification_router)
except ImportError:
    logger.warning("lawyer路由未加载")

# 知识库
try:
    from . import knowledge
    api_router.include_router(knowledge.router)
except ImportError:
    logger.warning("knowledge路由未加载")

# 通知
try:
    from . import notification
    api_router.include_router(notification.router)
    api_router.include_router(notification.admin_router)
except ImportError:
    logger.warning("notification路由未加载")

# 个人设置（Profile / 通知 / 隐私 / API Keys）
try:
    from . import settings
    api_router.include_router(settings.router)
except ImportError:
    logger.warning("settings路由未加载")

try:
    from . import ai_quality
    api_router.include_router(ai_quality.router)
except ImportError:
    logger.warning("ai_quality路由未加载")

try:
    from . import points
    api_router.include_router(points.router)
except ImportError:
    logger.warning("points路由未加载")

try:
    from . import recommendation
    api_router.include_router(recommendation.router)
except ImportError:
    logger.warning("recommendation路由未加载")

try:
    from . import moderation
    api_router.include_router(moderation.router)
except ImportError:
    logger.warning("moderation路由未加载")

try:
    from . import channel
    api_router.include_router(channel.router)
except ImportError:
    logger.warning("channel路由未加载")

# 文档与合同（本地 Mock）
try:
    from . import document
    api_router.include_router(document.router)
    api_router.include_router(document.contract_router)
except ImportError:
    logger.warning("document/contract路由未加载")

# ==========================================
# 微服务代理路由（业务逻辑在微服务中）— 注册在本地路由之后
# 测试环境下跳过代理注册，避免拦截本地路由
# ==========================================
import sys as _sys

if "pytest" not in _sys.modules:
    try:
        from .microservice_proxy import MICROSERVICES, create_proxy_router, router as proxy_router

        for service_name in MICROSERVICES.keys():
            router = create_proxy_router(service_name)
            api_router.include_router(router)
            logger.info(f"BFF代理路由已注册: {service_name}-service")
        api_router.include_router(proxy_router)
    except ImportError:
        logger.warning("微服务代理模块未加载")

__all__ = ["api_router"]
