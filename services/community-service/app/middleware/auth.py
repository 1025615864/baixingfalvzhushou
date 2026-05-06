"""认证中间件 - 从 APISIX Header 或 User Service 获取用户信息"""
from typing import Optional
from dataclasses import dataclass
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


@dataclass
class AuthUser:
    id: int
    role: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    is_lawyer: bool = False


class AuthMiddleware:
    def __init__(self, user_client=None):
        self.user_client = user_client

    async def get_current_user(self, request: Request) -> AuthUser:
        user_id = request.headers.get("X-User-ID")
        user_role = request.headers.get("X-User-Role", "user")

        if user_id:
            return AuthUser(
                id=int(user_id),
                role=user_role,
                is_lawyer=(user_role == "lawyer")
            )

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未登录或Token无效"
            )

        token = auth_header.replace("Bearer ", "")

        if self.user_client:
            user_info = await self.user_client.verify_token(token)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token验证失败"
                )
            return AuthUser(
                id=user_info["user_id"],
                role=user_info.get("role", "user"),
                nickname=user_info.get("nickname"),
                avatar=user_info.get("avatar"),
                is_lawyer=user_info.get("is_lawyer", False)
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证用户身份"
        )


security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,
    auth_middleware: AuthMiddleware = None
) -> Optional[AuthUser]:
    try:
        if auth_middleware:
            return await auth_middleware.get_current_user(request)
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return AuthUser(
                id=int(user_id),
                role=request.headers.get("X-User-Role", "user")
            )
        return None
    except HTTPException:
        return None


def require_auth(func):
    async def wrapper(request: Request, *args, **kwargs):
        auth_middleware = kwargs.get("auth_middleware")
        user = await auth_middleware.get_current_user(request)
        kwargs["current_user"] = user
        return await func(request, *args, **kwargs)
    return wrapper


def require_role(required_role: str):
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            auth_middleware = kwargs.get("auth_middleware")
            user = await auth_middleware.get_current_user(request)
            if user.role != required_role and user.role != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要 {required_role} 权限"
                )
            kwargs["current_user"] = user
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
