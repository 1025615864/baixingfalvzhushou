"""权限服务"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..utils.permissions import ROLE_PERMISSIONS, Permission, Role


@dataclass
class RoleInfo:
    name: str


_EXTRA_USER_ROLES: dict[int, set[str]] = {}
_EXTRA_PERMISSIONS: set[str] = set()


class PermissionService:
    async def _get_user(self, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == int(user_id)))
        return result.scalar_one_or_none()

    async def check_permission(
            self, db: AsyncSession, *, user_id: int, permission: str) -> bool:
        user = await self._get_user(db, user_id)
        if not user:
            return False
        perm = str(permission)
        if perm == "admin:all" and user.role in (Role.ADMIN, Role.SUPER_ADMIN):
            return True
        base_perms = ROLE_PERMISSIONS.get(user.role, set())
        extra_roles = _EXTRA_USER_ROLES.get(int(user.id), set())
        for role in extra_roles:
            base_perms = base_perms | ROLE_PERMISSIONS.get(role, set())
        if perm == "user:update":
            perm = Permission.USER_WRITE
        return perm in base_perms or perm in _EXTRA_PERMISSIONS

    async def get_user_roles(self, db: AsyncSession,
                             user_id: int) -> list[str]:
        user = await self._get_user(db, user_id)
        roles = [user.role] if user else []
        roles.extend(sorted(_EXTRA_USER_ROLES.get(int(user_id), set())))
        return roles

    async def assign_role(self, db: AsyncSession, *,
                          user_id: int, role: str) -> bool:
        user = await self._get_user(db, user_id)
        if not user:
            return False
        roles = _EXTRA_USER_ROLES.setdefault(int(user_id), set())
        roles.add(str(role))
        await db.commit()
        return True

    async def revoke_role(self, db: AsyncSession, *,
                          user_id: int, role: str) -> bool:
        roles = _EXTRA_USER_ROLES.get(int(user_id), set())
        roles.discard(str(role))
        await db.commit()
        return True

    async def check_role(self, db: AsyncSession, *,
                         user_id: int, role: str) -> bool:
        user = await self._get_user(db, user_id)
        if user and user.role == str(role):
            return True
        return str(role) in _EXTRA_USER_ROLES.get(int(user_id), set())

    async def get_role_permissions(self, role: str) -> list[str]:
        role_name = str(role)
        permissions = set(ROLE_PERMISSIONS.get(role_name, set()))
        if role_name == Role.USER:
            permissions.add("user:update")
        return sorted(permissions)

    async def create_permission(
        self,
        db: AsyncSession,
        *,
        name: str,
        description: str | None = None,
        category: str | None = None,
    ) -> bool:
        _EXTRA_PERMISSIONS.add(str(name))
        await db.commit()
        return True


permission_service = PermissionService()
