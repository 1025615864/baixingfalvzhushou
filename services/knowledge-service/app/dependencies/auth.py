"""知识库服务鉴权依赖"""
import os
import logging
from typing import Optional, List
from dataclasses import dataclass
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


@dataclass
class UserContext:
    user_id: int
    username: str = ""
    role: str = "user"


class AuthenticationError(Exception):
    pass


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def verify_token(token: str) -> Optional[UserContext]:
    """验证JWT token"""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        return UserContext(
            user_id=payload.get("user_id", 0),
            username=payload.get("username", ""),
            role=payload.get("role", "user")
        )
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> UserContext:
    """获取当前用户（必需认证）"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录才能访问",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user = verify_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[UserContext]:
    """获取当前用户（可选，不强制）"""
    if not credentials:
        return None

    token = credentials.credentials
    return verify_token(token)


def require_roles(*allowed_roles: str):
    """角色权限检查装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user: Optional[UserContext] = kwargs.get("current_user")
            if not user:
                for arg in args:
                    if isinstance(arg, UserContext):
                        user = arg
                        break

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录"
                )

            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要角色: {', '.join(allowed_roles)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_permission(role: str, resource: str, action: str) -> bool:
    """检查权限"""
    permissions = {
        "ai_knowledge_director": {
            "knowledge": ["create", "read", "update", "delete", "publish"],
            "archive": ["create", "read", "update", "delete", "publish"],
            "ai_config": ["read", "update"],
            "ai_quality": ["read"]
        },
        "knowledge_editor": {
            "knowledge": ["create", "read", "update", "delete"],
            "archive": ["read"],
            "ai_config": [],
            "ai_quality": []
        },
        "archive_editor": {
            "knowledge": ["read"],
            "archive": ["create", "read", "update", "delete"],
            "ai_config": [],
            "ai_quality": []
        },
        "ai_quality_operator": {
            "knowledge": ["read"],
            "archive": ["read"],
            "ai_config": ["read", "update"],
            "ai_quality": ["read", "update"]
        },
        "admin": {
            "knowledge": ["create", "read", "update", "delete", "publish"],
            "archive": ["create", "read", "update", "delete", "publish"],
            "ai_config": ["read", "update"],
            "ai_quality": ["read", "update"]
        },
        "user": {
            "knowledge": ["read"],
            "archive": ["read"],
            "ai_config": [],
            "ai_quality": []
        }
    }

    role_permissions = permissions.get(role, {})
    resource_permissions = role_permissions.get(resource, [])
    return action in resource_permissions
