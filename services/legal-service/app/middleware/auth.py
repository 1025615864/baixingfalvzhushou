"""认证中间件 - 从 APISIX Header 或 User Service 获取用户信息"""
import os
from typing import Optional
from dataclasses import dataclass
from fastapi import HTTPException, Request, status
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
        self._grpc_client = None
        self._use_grpc = os.getenv("USER_SERVICE_GRPC_ENABLED", "false").lower() in {"1", "true", "yes"}
        if self._use_grpc:
            from app.clients import user_grpc_client
            self._grpc_client = user_grpc_client

    async def _validate_token_grpc(self, token: str) -> Optional[AuthUser]:
        if not self._grpc_client:
            return None
        try:
            result = await self._grpc_client.validate_token(token)
            if result and result.get("valid"):
                return AuthUser(
                    id=result["user_id"],
                    role=result["roles"][0] if result.get("roles") else "user",
                    is_lawyer=("lawyer" in result.get("roles", []))
                )
        except Exception as e:
            pass
        return None

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

        if self._use_grpc and self._grpc_client:
            user = await self._validate_token_grpc(token)
            if user:
                return user

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
            detail="无法验证用户身份: 用户服务不可用"
        )


auth_middleware = AuthMiddleware()


async def get_current_user(request: Request) -> AuthUser:
    return await auth_middleware.get_current_user(request)


async def get_current_user_optional(request: Request) -> Optional[AuthUser]:
    try:
        return await auth_middleware.get_current_user(request)
    except HTTPException:
        return None


async def get_current_lawyer(request: Request) -> AuthUser:
    user = await get_current_user(request)
    if user.role != "lawyer" and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要律师身份"
        )
    return user


async def get_admin_user(request: Request) -> AuthUser:
    user = await get_current_user(request)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user


async def get_platform_firm_admin(request: Request) -> AuthUser:
    """获取平台律所管理员"""
    user = await get_current_user(request)
    if user.role not in ["admin", "platform_firm_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要平台律所管理员权限"
        )
    return user


async def get_firm_admin(request: Request) -> AuthUser:
    """获取律所管理员"""
    user = await get_current_user(request)
    if user.role not in ["admin", "platform_firm_admin", "lawfirm_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要律所管理员权限"
        )
    return user


async def require_firm_admin_of(firm_id: int, db):
    """检查用户是否是指定律所的管理员"""
    from ..services.firm_service import FirmService
    user = await get_current_user_from_request()
    if user.role in ["admin", "platform_firm_admin"]:
        return user
    service = FirmService(db)
    if not await service.is_firm_admin(firm_id, user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要是该律所的管理员"
        )
    return user


async def get_current_user_from_request() -> AuthUser:
    """从请求中获取当前用户 - 供内部使用"""
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    security = HTTPBearer(auto_error=False)


from functools import wraps
from typing import List
from fastapi import Depends

from ..shared.permissions import Permission, get_permissions_for_role


class PermissionChecker:
    """权限检查器 - 声明式权限依赖"""

    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions

    async def __call__(
        self,
        request: Request,
        current_user: AuthUser = Depends(get_current_user)
    ):
        user_permissions = get_permissions_for_role(current_user.role)

        for perm in self.required_permissions:
            if perm not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要权限: {perm.value}"
                )

        return current_user


def require_permissions(*permissions: Permission):
    """权限检查依赖工厂"""
    async def dependency(current_user: AuthUser = Depends(get_current_user)):
        user_permissions = get_permissions_for_role(current_user.role)
        for perm in permissions:
            if perm not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要权限: {perm.value}"
                )
        return current_user
    return dependency