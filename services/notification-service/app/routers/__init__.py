"""通知服务路由"""
from .notification import router as notification_router
from .admin import router as admin_router

__all__ = ["notification_router", "admin_router"]
