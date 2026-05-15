"""统一管理员认证中间件 - 支持业务域隔离的并行角色体系

角色体系：
- 全局角色：super_admin, admin（跨域管理，可访问所有业务域管理路由）
- 业务域角色：每个域有独立的 admin + ops 角色
  - legal_admin/legal_ops/lawfirm_owner
  - news_admin/news_ops
  - community_admin/community_ops/community_cs
  - 等等

用法：
  # 要求任意管理员角色
  @router.get("/", dependencies=[Depends(get_admin_user)])

  # 要求特定业务域角色
  @router.get("/", dependencies=[Depends(require_domain_role("legal"))])
  @router.get("/", dependencies=[Depends(require_domain_role("legal", roles=["legal_admin"]))])

  # 要求特定权限
  @router.get("/", dependencies=[Depends(require_permission("lawyer:verify"))])
"""
import logging
import os
from typing import Optional, List, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from services.common.middleware.auth import verify_token, TokenPayload

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

GLOBAL_ADMIN_ROLES = {"super_admin", "admin"}

ALL_ADMIN_ROLE_CODES = {
    "super_admin", "admin",
    "legal_admin", "legal_ops", "lawfirm_owner",
    "news_admin", "news_ops",
    "community_admin", "community_ops", "community_cs",
    "order_admin", "order_ops",
    "payment_admin", "payment_ops",
    "knowledge_admin", "knowledge_ops",
    "archive_admin", "archive_ops",
    "notification_admin", "notification_ops",
    "embedding_admin",
    "ai_admin", "ai_ops",
    "search_admin", "search_ops",
}

DOMAIN_ROLES: dict[str, Set[str]] = {
    "global": {"super_admin", "admin"},
    "legal": {"legal_admin", "legal_ops", "lawfirm_owner"},
    "news": {"news_admin", "news_ops"},
    "community": {"community_admin", "community_ops", "community_cs"},
    "order": {"order_admin", "order_ops"},
    "payment": {"payment_admin", "payment_ops"},
    "knowledge": {"knowledge_admin", "knowledge_ops"},
    "archive": {"archive_admin", "archive_ops"},
    "notification": {"notification_admin", "notification_ops"},
    "embedding": {"embedding_admin"},
    "ai": {"ai_admin", "ai_ops"},
    "points": {"points_admin", "points_ops"},
}

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "internal-api-key-change-in-production")


class AdminUser:
    """管理员用户信息 - 支持业务域角色"""

    def __init__(
        self,
        user_id: int,
        role: str,
        domain: str = "global",
        permissions: Optional[List[str]] = None,
        scope_id: Optional[int] = None,
    ):
        self.user_id = user_id
        self.role = role
        self.domain = domain
        self.permissions = permissions or []
        self.scope_id = scope_id
        self.is_super_admin = role in GLOBAL_ADMIN_ROLES

    def has_permission(self, permission: str) -> bool:
        if self.is_super_admin:
            return True
        return permission in self.permissions

    def has_any_permission(self, *permissions: str) -> bool:
        if self.is_super_admin:
            return True
        return bool(set(permissions) & set(self.permissions))

    def has_domain_access(self, domain: str) -> bool:
        if self.is_super_admin:
            return True
        domain_roles = DOMAIN_ROLES.get(domain, set())
        return self.role in domain_roles

    def is_domain_admin(self, domain: str) -> bool:
        if self.is_super_admin:
            return True
        domain_roles = DOMAIN_ROLES.get(domain, set())
        admin_roles = {r for r in domain_roles if r.endswith("_admin")}
        return self.role in admin_roles

    def __repr__(self) -> str:
        return f"<AdminUser(id={self.user_id}, role={self.role}, domain={self.domain})>"


def _payload_to_admin(payload) -> Optional[AdminUser]:
    """将 JWT payload 转换为 AdminUser"""
    user_role = payload.get("role", "user")
    if user_role not in ALL_ADMIN_ROLE_CODES:
        return None

    return AdminUser(
        user_id=payload.get("user_id") or int(payload.get("sub", 0)),
        role=user_role,
        domain=payload.get("domain", "global"),
        permissions=payload.get("permissions", []),
        scope_id=payload.get("scope_id"),
    )


async def get_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AdminUser:
    """获取管理员用户（必需管理员角色）"""
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

    admin = _payload_to_admin(payload)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"需要管理员角色，当前角色: {payload.get('role', 'user')}",
        )

    return admin


async def get_optional_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[AdminUser]:
    """获取管理员用户（可选，不强制）"""
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        return None

    return _payload_to_admin(payload)


def require_domain_role(domain: str, roles: Optional[List[str]] = None):
    """要求特定业务域的管理角色

    用法:
        # 要求 legal 域任意管理角色
        @router.get("/", dependencies=[Depends(require_domain_role("legal"))])

        # 要求 legal 域的 admin 角色
        @router.get("/", dependencies=[Depends(require_domain_role("legal", roles=["legal_admin"]))])
    """
    async def domain_checker(admin: AdminUser = Depends(get_admin_user)):
        if admin.is_super_admin:
            return admin

        if not admin.has_domain_access(domain):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {domain} 域管理角色，当前角色: {admin.role}",
            )

        if roles and admin.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色: {', '.join(roles)}，当前角色: {admin.role}",
            )

        return admin

    return domain_checker


def require_admin_role(*allowed_roles: str):
    """要求特定管理员角色

    用法:
        @router.get("/", dependencies=[Depends(require_admin_role("super_admin", "legal_admin"))])
    """
    async def role_checker(admin: AdminUser = Depends(get_admin_user)):
        if admin.is_super_admin:
            return admin
        if admin.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色: {', '.join(allowed_roles)}，当前角色: {admin.role}",
            )
        return admin

    return role_checker


def require_permission(permission: str):
    """要求特定权限

    用法:
        @router.get("/", dependencies=[Depends(require_permission("lawyer:verify"))])
    """
    async def permission_checker(admin: AdminUser = Depends(get_admin_user)):
        if not admin.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要权限: {permission}",
            )
        return admin

    return permission_checker
