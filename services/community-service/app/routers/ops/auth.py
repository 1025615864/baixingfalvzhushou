"""运营认证与角色管理路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.ops.ops_auth_service import OpsAuthService
from app.middleware.ops_auth import require_ops_role

router = APIRouter(prefix="/api/v1/community/ops", tags=["运营认证"])


class AssignRoleRequest(BaseModel):
    user_id: int
    role: str


class RoleResponse(BaseModel):
    id: int
    user_id: int
    role: str
    is_active: bool


@router.post("/auth/login")
async def ops_login(request: Request):
    return {"success": True, "message": "运营登录成功"}


@router.get("/roles")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("community_director"))
):
    service = OpsAuthService(db)
    ops_users = await service.list_ops_users()
    return {
        "success": True,
        "data": [
            {
                "id": u.id,
                "user_id": u.user_id,
                "role": u.role,
                "is_active": u.is_active,
                "assigned_by": u.assigned_by,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in ops_users
        ]
    }


@router.post("/roles/assign")
async def assign_role(
    req: AssignRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("community_director"))
):
    service = OpsAuthService(db)
    ops_role = await service.assign_role(
        user_id=req.user_id,
        role=req.role,
        assigned_by=current_user["id"]
    )
    return {"success": True, "message": "角色分配成功", "data": {"id": ops_role.id}}


@router.delete("/roles/{user_id}")
async def revoke_role(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("community_director"))
):
    service = OpsAuthService(db)
    success = await service.revoke_role(user_id=user_id, revoked_by=current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="未找到运营角色")
    return {"success": True, "message": "角色已撤销"}


@router.get("/roles/permissions")
async def get_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("community_director", "content_mod", "topic_ops", "user_ops", "data_analyst"))
):
    service = OpsAuthService(db)
    roles = await service.get_all_roles()
    return {"success": True, "data": roles}
