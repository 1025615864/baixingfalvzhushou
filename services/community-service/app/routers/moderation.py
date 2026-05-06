"""审核管理路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.moderation_queue_service import ModerationService
from ..schemas.common_schema import ListResponse, SuccessResponse
from ..middleware.auth import AuthMiddleware, AuthUser
from ..clients import user_service_client

router = APIRouter(prefix="/moderation", tags=["审核管理"])

auth_middleware = AuthMiddleware(user_client=user_service_client)


class ModerationItemResponse:
    pass


@router.get("/queue", response_model=ListResponse)
async def get_moderation_queue(
    request: Request,
    status: Optional[str] = Query(None, description="pending/reviewed"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = ModerationService(db)
    items, total = await service.get_queue(page=page, page_size=page_size, status=status)
    return ListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/queue/{item_id}")
async def get_moderation_item(
    request: Request,
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = ModerationService(db)
    item = await service.get_queue_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="审核项不存在")
    return {"success": True, "data": item}


@router.post("/queue/{item_id}")
async def review_moderation_item(
    request: Request,
    item_id: int,
    decision: str = Query(..., regex="^(approve|reject|modify)$"),
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = ModerationService(db)
    item = await service.review(
        item_id=item_id,
        decision=decision,
        reviewer_id=current_user.id,
        reason=reason
    )
    return {"success": True, "message": f"审核完成: {decision}", "data": item}


@router.get("/stats")
async def get_moderation_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = ModerationService(db)
    stats = await service.get_stats()
    return {"success": True, "data": stats}
