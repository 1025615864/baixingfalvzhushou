"""内容审核工作台路由"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.ops.content_ops_service import ContentOpsService
from app.services.ops.audit_service import AuditService
from app.middleware.ops_auth import require_ops_role, log_audit

try:
    from services.common.middleware.admin_auth import require_domain_role
except ImportError:
    from fastapi import Depends, HTTPException
    def require_domain_role(domain: str, roles=None):
        async def _checker(request=None):
            from fastapi import Request
            if request and hasattr(request, 'headers'):
                role = request.headers.get("X-Admin-Role", "")
                if role in {"super_admin", "admin"}:
                    return None
                if roles and role not in roles:
                    raise HTTPException(status_code=403, detail=f"需要角色: {', '.join(roles)}")
            return None
        return _checker

router = APIRouter(prefix="/api/v1/community/ops/content", tags=["内容审核工作台"], dependencies=[Depends(require_domain_role("community", roles=["community_ops"]))])


class ReviewRequest(BaseModel):
    action: str
    reason: Optional[str] = None
    modified_content: Optional[str] = None
    penalty: Optional[str] = None


class BatchReviewRequest(BaseModel):
    ids: List[int]
    action: str
    reason: Optional[str] = None


class AssignRequest(BaseModel):
    assignee_id: int


@router.get("/queue")
async def get_review_queue(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director"))
):
    service = ContentOpsService(db)
    items, total = await service.get_review_queue(
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        page=page,
        page_size=page_size
    )
    return {
        "success": True,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/queue/{queue_id}")
async def get_review_detail(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director"))
):
    service = ContentOpsService(db)
    detail = await service.get_review_detail(queue_id)
    if not detail:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="审核项不存在")
    return {"success": True, "data": detail}


@router.post("/queue/{queue_id}/review")
async def review_content(
    queue_id: int,
    req: ReviewRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director"))
):
    service = ContentOpsService(db)
    result = await service.review_content(
        queue_id=queue_id,
        action=req.action,
        reason=req.reason,
        modified_content=req.modified_content,
        penalty=req.penalty,
        operator_id=current_user["id"],
        operator_role=current_user.get("ops_role", "content_mod")
    )

    await log_audit(
        request=request,
        action=f"review_{req.action}",
        target_type="moderation_queue",
        target_id=queue_id,
        detail=req.reason
    )

    return {"success": True, "message": f"审核操作【{req.action}】完成", "data": result}


@router.post("/queue/batch-review")
async def batch_review(
    req: BatchReviewRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director"))
):
    service = ContentOpsService(db)
    result = await service.batch_review(
        queue_ids=req.ids,
        action=req.action,
        reason=req.reason,
        operator_id=current_user["id"],
        operator_role=current_user.get("ops_role", "content_mod")
    )

    for queue_id in req.ids:
        await log_audit(
            request=request,
            action=f"batch_review_{req.action}",
            target_type="moderation_queue",
            target_id=queue_id,
            detail=req.reason
        )

    return {"success": True, "message": f"批量审核完成，成功{result['success_count']}条"}


@router.post("/queue/{queue_id}/assign")
async def assign_review(
    queue_id: int,
    req: AssignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director"))
):
    service = ContentOpsService(db)
    await service.assign_reviewer(queue_id, req.assignee_id, current_user["id"])

    await log_audit(
        request=request,
        action="assign_reviewer",
        target_type="moderation_queue",
        target_id=queue_id,
        detail=f"分配给用户 {req.assignee_id}"
    )

    return {"success": True, "message": "已分配审核任务"}


@router.get("/stats")
async def get_moderation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("content_mod", "community_director", "data_analyst"))
):
    service = ContentOpsService(db)
    stats = await service.get_moderation_stats()
    return {"success": True, "data": stats}
