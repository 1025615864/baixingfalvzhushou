"""运营路由模块"""
from app.routers.ops.auth import router as ops_auth_router
from app.routers.ops.audit_log import router as audit_log_router
from app.routers.ops.content import router as content_ops_router
from app.routers.ops.user_ops import router as user_ops_router
from app.routers.ops.topic_ops import router as topic_ops_router
from app.routers.ops.analytics import router as analytics_ops_router
from app.routers.ops.config import router as config_ops_router
from app.routers.ops.announcement import router as announcement_router

__all__ = [
    "ops_auth_router",
    "audit_log_router",
    "content_ops_router",
    "user_ops_router",
    "topic_ops_router",
    "analytics_ops_router",
    "config_ops_router",
    "announcement_router",
]
