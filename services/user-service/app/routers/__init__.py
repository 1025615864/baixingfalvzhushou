"""用户服务路由"""
from .auth import router as auth_router
from .user import router as user_router
from .profile import router as profile_router

__all__ = ["auth_router", "user_router", "profile_router"]
