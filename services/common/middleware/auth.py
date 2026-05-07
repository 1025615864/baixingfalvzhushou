"""统一认证中间件

所有微服务和 BFF 共享同一认证栈。
使用 JWTKeyManager 支持 RS256/HS256 统一解码，自动尝试多密钥。
"""
import logging
import os
from typing import Optional, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps

from services.common.security.jwt_manager import JWTKeyManager

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

_jwt_manager: Optional[JWTKeyManager] = None


def get_jwt_manager(db_session_factory=None) -> JWTKeyManager:
    """获取或创建 JWT 密钥管理器单例"""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTKeyManager(
            db_session_factory=db_session_factory,
            rotation_days=int(os.getenv("JWT_ROTATION_DAYS", "90")),
            grace_period_days=int(os.getenv("JWT_GRACE_PERIOD_DAYS", "7")),
        )
    return _jwt_manager


def reset_jwt_manager():
    """重置 JWT 管理器（仅用于测试）"""
    global _jwt_manager
    _jwt_manager = None


def verify_token(token: str) -> Optional[dict]:
    """验证 JWT token（支持 RS256 多密钥和 HS256 fallback）"""
    try:
        manager = get_jwt_manager()
        payload = manager.decode_token(token)
        if payload:
            return payload
    except Exception as e:
        logger.warning(f"JWTKeyManager decode failed: {e}")

    # Fallback: 尝试环境变量中的 HS256 密钥
    hs256_secret = os.getenv("JWT_SECRET_KEY", "")
    if hs256_secret:
        try:
            from jose import jwt
            payload = jwt.decode(token, hs256_secret, algorithms=["HS256"])
            return payload
        except Exception as e:
            logger.warning(f"HS256 fallback decode failed: {e}")

    return None


class TokenPayload:
    """Token 载荷（兼容旧接口）"""

    def __init__(self, user_id: int, role: str, exp: int = None):
        self.user_id = user_id
        self.role = role
        self.exp = exp

    @classmethod
    def from_dict(cls, data: dict) -> "TokenPayload":
        """从字典创建 TokenPayload"""
        return cls(
            user_id=data.get("user_id") or data.get("sub"),
            role=data.get("role", "user"),
            exp=data.get("exp"),
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """获取当前用户（必需认证）"""
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

    return TokenPayload.from_dict(payload)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenPayload]:
    """获取当前用户（可选认证）"""
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_token(token)
    if payload:
        return TokenPayload.from_dict(payload)
    return None


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

    expire = datetime.utcnow() + timedelta(minutes=60)
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "role": role,
        "exp": int(expire.timestamp()),
    }

    manager = get_jwt_manager()
    try:
        return manager.create_token(payload, expires_minutes=60)
    except Exception:
        # Fallback to HS256 if JWTKeyManager fails
        from jose import jwt

        hs256_secret = os.getenv("JWT_SECRET_KEY", "test-secret")
        return jwt.encode(payload, hs256_secret, algorithm="HS256")


def create_token_payload(
    user_id: int, role: str = "user", sub: str = None, **extra
) -> dict:
    """创建 token payload 字典（推荐用于微服务间调用）"""
    return {
        "sub": sub or str(user_id),
        "user_id": user_id,
        "role": role,
        **extra,
    }


ROLES = {
    "ai_knowledge_director": "AI知识库主管",
    "knowledge_editor": "知识编辑",
    "archive_editor": "案例编辑",
    "ai_quality_operator": "AI质量运营",
    "admin": "系统管理员",
    "user": "普通用户",
}


def check_permission(role: str, resource: str, action: str) -> bool:
    """检查权限"""
    permissions = {
        "ai_knowledge_director": {
            "knowledge": ["create", "read", "update", "delete", "publish"],
            "archive": ["create", "read", "update", "delete", "publish"],
            "ai_config": ["read", "update"],
            "ai_quality": ["read"],
        },
        "knowledge_editor": {
            "knowledge": ["create", "read", "update", "delete"],
            "archive": ["read"],
            "ai_config": [],
            "ai_quality": [],
        },
        "archive_editor": {
            "knowledge": ["read"],
            "archive": ["create", "read", "update", "delete"],
            "ai_config": [],
            "ai_quality": [],
        },
        "ai_quality_operator": {
            "knowledge": ["read"],
            "archive": ["read"],
            "ai_config": ["read", "update"],
            "ai_quality": ["read", "update"],
        },
        "admin": {
            "knowledge": ["create", "read", "update", "delete", "publish"],
            "archive": ["create", "read", "update", "delete", "publish"],
            "ai_config": ["read", "update"],
            "ai_quality": ["read", "update"],
        },
        "user": {
            "knowledge": ["read"],
            "archive": ["read"],
            "ai_config": [],
            "ai_quality": [],
        },
    }

    role_permissions = permissions.get(role, {})
    resource_permissions = role_permissions.get(resource, [])
    return action in resource_permissions
