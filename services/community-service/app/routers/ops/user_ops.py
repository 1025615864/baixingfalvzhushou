"""用户运营路由"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.ops.user_ops_service import UserOpsService
from app.services.ops.audit_service import AuditService
from app.middleware.ops_auth import require_ops_role, log_audit

router = APIRouter(prefix="/api/v1/community/ops/users", tags=["用户运营"])


class PenaltyRequest(BaseModel):
    type: str
    duration_hours: Optional[int] = None
    reason: Optional[str] = None
    related_post_id: Optional[int] = None
    notify_user: bool = True


class AppealHandleRequest(BaseModel):
    action: str
    reason: Optional[str] = None


class NotifyRequest(BaseModel):
    title: str
    content: str
    type: str = "info"


class BroadcastRequest(BaseModel):
    target: str = "all"
    title: str
    content: str


@router.get("/search")
async def search_users(
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("user_ops", "community_director"))
):
    return {
        "success": True,
        "data": {"items": [], "total": 0, "page": page, "page_size": page_size}
    }


@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("user_ops", "content_mod", "community_director"))
):
    service = UserOpsService(db)
    profile = await service.get_user_profile(user_id)
    return {"success": True, "data": profile}


@router.get("/{user_id}/violations")
async def get_user_violations(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("user_ops", "content_mod", "community_director"))
):
    service = UserOpsService(db)
    penalties = await service.get_user_penalties(user_id, include_inactive=True)
    return {
        "success": True,
        "data": [
            {
                "id": p.id,
                "type": p.type,
                "reason": p.reason,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "expires_at": p.expires_at.isoformat() if p.expires_at else None
            }
            for p in penalties
        ]
    }


@router.post("/{user_id}/penalty")
async def penalize_user(
    user_id: int,
    req: PenaltyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("user_ops", "content_mod", "community_director"))
):
    service = UserOpsService(db)
    penalty = await service.penalize_user(
        user_id=user_id,
        penalty_type=req.type,
        reason=req.reason,
        duration_hours=req.duration_hours,
        related_post_id=req.related_post_id,
        operator_id=current_user["id"]
    )

    await log_audit(
        request=request,
        action=f"penalty_{req.type}",
        target_type="user",
        target_id=user_id,
        detail=req.reason
    )

    return {"success": True, "message": f"用户已被【{req.type}】"}


@router.delete("/{user_id}/penalty")
async def revoke_penalty(
    user_id: int,
    request: Request,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("user_ops", "community_director"))
):
    service = UserOpsService(db)
    success = await service.revoke_penalty(
        user_id=user_id,
        revoked_by=current_user["id"],
        reason=reason
    )

    await log_audit(
        request=request,
        action="revoke_penalty",
        target_type="user",
        target_id=user_id,
        detail=reason
    )

    return {"success": True, "message": "处罚已解除"}


@router.get("/appeals")
async def get_appeals(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("user_ops", "community_director"))
):
    service = UserOpsService(db)
    appeals, total = await service.get_user_appeals(status=status, page=page, page_size=page_size)
    return {
        "success": True,
        "data": {"items": appeals, "total": total, "page": page, "page_size": page_size}
    }


@router.post("/appeals/{appeal_id}/handle")
async def handle_appeal(
    appeal_id: int,
    req: AppealHandleRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("user_ops", "community_director"))
):
    service = UserOpsService(db)
    success = await service.handle_appeal(
        appeal_id=appeal_id,
        action=req.action,
        handle_reason=req.reason,
        handler_id=current_user["id"]
    )

    await log_audit(
        request=request,
        action=f"appeal_{req.action}",
        target_type="user_appeal",
        target_id=appeal_id,
        detail=req.reason
    )

    return {"success": True, "message": f"申诉已【{'通过' if req.action == 'accept' else '拒绝'}】"}


@router.post("/{user_id}/notify")
async def notify_user(
    user_id: int,
    req: NotifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("user_ops", "community_director"))
):
    await log_audit(
        request=request,
        action="notify_user",
        target_type="user",
        target_id=user_id,
        detail=f"{req.title}: {req.content}"
    )
    return {"success": True, "message": "通知已发送"}


@router.post("/broadcast")
async def broadcast(
    req: BroadcastRequest,
    request: Request,
    current_user: dict = Depends(require_ops_role("user_ops", "community_director"))
):
    await log_audit(
        request=request,
        action="broadcast",
        target_type="system",
        detail=f"{req.title}: {req.content}"
    )
    return {"success": True, "message": "广播已发送"}
