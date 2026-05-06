"""AI服务依赖模块"""
from app.dependencies.auth import (
    AuthDependency,
    UserContext,
    get_current_user,
    get_required_user,
    require_admin,
    require_role,
    require_permission,
    AuthenticationError,
    AuthorizationError,
)

__all__ = [
    "AuthDependency",
    "UserContext",
    "get_current_user",
    "get_required_user",
    "require_admin",
    "require_role",
    "require_permission",
    "AuthenticationError",
    "AuthorizationError",
]
