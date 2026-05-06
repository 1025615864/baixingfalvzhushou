"""统一鉴权依赖模块"""
import logging
from typing import Optional, List
from dataclasses import dataclass
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


@dataclass
class UserContext:
    user_id: int
    username: str
    role: str
    permissions: List[str]


class AuthenticationError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class AuthDependency:
    """统一鉴权依赖"""

    def __init__(self):
        self._public_key = None
        self._user_service_url = settings.user_service_url
        self._verify_url = f"{self._user_service_url}/api/v1/auth/verify"

    async def get_current_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
    ) -> UserContext:
        """获取当前用户（可选认证）"""
        if not credentials:
            return self._get_anonymous_user()

        token = credentials.credentials

        try:
            user_info = await self._verify_token(token)
            return UserContext(
                user_id=user_info.get("user_id", 0),
                username=user_info.get("username", ""),
                role=user_info.get("role", "user"),
                permissions=user_info.get("permissions", [])
            )
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token无效或已过期"
            )

    async def get_required_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
    ) -> UserContext:
        """获取当前用户（必须登录）"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要登录才能访问"
            )

        return await self.get_current_user(credentials)

    def require_admin(self, user: UserContext = Depends(get_current_user)) -> UserContext:
        """要求管理员权限"""
        if user.role not in ("admin", "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
        return user

    def require_role(self, allowed_roles: List[str]):
        """要求指定角色"""
        def decorator(user: UserContext = Depends(self.get_current_user)) -> UserContext:
            if user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下角色之一: {', '.join(allowed_roles)}"
                )
            return user
        return decorator

    def require_permission(self, permission: str):
        """要求指定权限"""
        def decorator(user: UserContext = Depends(self.get_current_user)) -> UserContext:
            if permission not in user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少必要权限: {permission}"
                )
            return user
        return decorator

    async def _verify_token(self, token: str) -> dict:
        """验证Token"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self._verify_url,
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise AuthenticationError("Token已过期")
                else:
                    raise AuthenticationError(f"验证失败: {response.status_code}")

        except httpx.TimeoutException:
            logger.error("Token verification timeout")
            raise AuthenticationError("验证服务超时")
        except httpx.RequestError as e:
            logger.error(f"Token verification request error: {e}")
            raise AuthenticationError("验证服务不可用")

    def _get_anonymous_user(self) -> UserContext:
        """获取匿名用户"""
        return UserContext(
            user_id=0,
            username="anonymous",
            role="guest",
            permissions=[]
        )


auth_dependency = AuthDependency()

get_current_user = auth_dependency.get_current_user
get_required_user = auth_dependency.get_required_user
require_admin = auth_dependency.require_admin
require_role = auth_dependency.require_role
require_permission = auth_dependency.require_permission
