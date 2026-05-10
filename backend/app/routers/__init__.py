"""API路由 - BFF 聚合层

⚠️ Backend 作为 BFF 层，不再直接包含业务逻辑。
⚠️ 业务逻辑已迁移到对应微服务，此处仅负责路由转发和数据聚合。
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

api_router = APIRouter()

# ==========================================
# 微服务代理路由（业务逻辑在微服务中）
# ==========================================
try:
    from .microservice_proxy import MICROSERVICES, create_proxy_router, router as proxy_router

    for service_name in MICROSERVICES.keys():
        router = create_proxy_router(service_name)
        api_router.include_router(router)
        logger.info(f"BFF代理路由已注册: {service_name}-service")
    api_router.include_router(proxy_router)
except ImportError:
    logger.warning("微服务代理模块未加载")

# ==========================================
# 本地保留路由（BFF 职责范围内）
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

# WebSocket（实时通信基础设施）
try:
    from . import websocket
    api_router.include_router(websocket.router)
except ImportError:
    logger.warning("websocket路由未加载")

try:
    from . import ai
    api_router.include_router(ai.router)
except ImportError:
    logger.warning("ai路由未加载")

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
    from . import search
    api_router.include_router(search.router)
except ImportError:
    logger.warning("search路由未加载")

try:
    from . import forum
    api_router.include_router(forum.router)
except ImportError:
    logger.warning("forum路由未加载")

__all__ = ["api_router"]
