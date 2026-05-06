"""运营认证服务"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import HTTPException

from app.models.ops_models import OpsRole, VALID_OPS_ROLES


class OpsAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_role(self, user_id: int) -> Optional[OpsRole]:
        result = await self.db.execute(
            select(OpsRole).where(
                OpsRole.user_id == user_id,
                OpsRole.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def assign_role(
        self,
        user_id: int,
        role: str,
        assigned_by: int
    ) -> OpsRole:
        if role not in VALID_OPS_ROLES:
            raise HTTPException(status_code=400, detail=f"无效的角色: {role}")

        existing = await self.get_user_role(user_id)

        if existing:
            if existing.role == role:
                raise HTTPException(status_code=400, detail="该用户已有此角色")

            existing.role = role
            existing.assigned_by = assigned_by
            existing.is_active = True
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        ops_role = OpsRole(
            user_id=user_id,
            role=role,
            assigned_by=assigned_by,
            is_active=True
        )
        self.db.add(ops_role)
        await self.db.commit()
        await self.db.refresh(ops_role)
        return ops_role

    async def revoke_role(self, user_id: int, revoked_by: int) -> bool:
        result = await self.db.execute(
            update(OpsRole)
            .where(OpsRole.user_id == user_id, OpsRole.is_active == True)
            .values(is_active=False)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def list_ops_users(self) -> List[OpsRole]:
        result = await self.db.execute(
            select(OpsRole).where(OpsRole.is_active == True)
        )
        return list(result.scalars().all())

    async def get_permissions_for_role(self, role: str) -> List[str]:
        return VALID_OPS_ROLES.get(role, [])

    async def get_all_roles(self) -> dict:
        return {
            role: {
                "permissions": VALID_OPS_ROLES.get(role, []),
                "description": self._get_role_description(role)
            }
            for role in VALID_OPS_ROLES
        }

    def _get_role_description(self, role: str) -> str:
        descriptions = {
            "community_director": "社区运营总监（全局权限）",
            "content_mod": "内容审核员",
            "topic_ops": "话题运营",
            "user_ops": "用户运营",
            "data_analyst": "数据分析师",
        }
        return descriptions.get(role, "")
