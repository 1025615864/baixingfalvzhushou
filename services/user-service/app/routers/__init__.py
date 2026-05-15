"""路由模块"""
from .auth import router as auth_router
from .user import router as user_router
from .profile import router as profile_router
from .membership import router as membership_router
from .ai_session import router as ai_session_router
from .password_reset import router as password_reset_router
from .account import router as account_router
from .data_export import router as data_export_router
from .email_verification import router as email_verification_router
from .device import router as device_router
from .admin import router as admin_router
from .agent import router as agent_router

__all__ = [
    "auth_router",
    "user_router",
    "profile_router",
    "membership_router",
    "ai_session_router",
    "password_reset_router",
    "account_router",
    "data_export_router",
    "email_verification_router",
    "device_router",
    "admin_router",
    "agent_router",
]
