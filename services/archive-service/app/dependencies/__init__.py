"""档案库服务依赖模块"""
from app.dependencies.auth import (
    UserContext,
    get_current_user,
    get_optional_user,
    check_permission,
    AuthenticationError,
)

__all__ = [
    "UserContext",
    "get_current_user",
    "get_optional_user",
    "check_permission",
    "AuthenticationError",
]
