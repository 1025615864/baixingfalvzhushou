"""统一认证中间件"""
import logging
import os
from typing import Optional, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from functools import wraps

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class AuthConfig:
    """认证配置"""
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))


config = AuthConfig()


class TokenPayload:
    """Token载荷"""
    def __init__(self, user_id: int, role: str, exp: int = None):
        self.user_id = user_id
        self.role = role
        self.exp = exp


def verify_token(token: str) -> Optional[TokenPayload]:
    """验证JWT token"""
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )
        return TokenPayload(
            user_id=payload.get("user_id"),
            role=payload.get("role", "user"),
            exp=payload.get("exp")
        )
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """获取当前用户（必需）"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenPayload]:
    """获取当前用户（可选）"""
    if not credentials:
        return None

    token = credentials.credentials
    return verify_token(token)


def require_roles(*allowed_roles: str):
    """角色权限装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证"
                )

            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要角色: {', '.join(allowed_roles)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def create_access_token(user_id: int, role: str = "user") -> str:
    """创建访问令牌（用于测试）"""
    from datetime import datetime, timedelta

    expire = datetime.utcnow() + timedelta(minutes=config.JWT_EXPIRATION_MINUTES)
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": int(expire.timestamp())
    }

    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


ROLES = {
    "ai_knowledge_director": "AI知识库主管",
    "knowledge_editor": "知识编辑",
    "archive_editor": "案例编辑",
    "ai_quality_operator": "AI质量运营",
    "admin": "系统管理员",
    "user": "普通用户"
}


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
