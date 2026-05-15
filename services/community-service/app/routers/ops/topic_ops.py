"""话题运营路由"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.ops.topic_ops_service import TopicOpsService
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

router = APIRouter(prefix="/api/v1/community/ops/topics", tags=["话题运营"], dependencies=[Depends(require_domain_role("community", roles=["community_ops"]))])


class PinRequest(BaseModel):
    duration_hours: int = 72


class SlotRequest(BaseModel):
    position: int
    post_id: int
    label: Optional[str] = None
    duration_hours: Optional[int] = None


class SlotsUpdateRequest(BaseModel):
    slots: list[SlotRequest]


class AnnouncementRequest(BaseModel):
    content: str


@router.post("/posts/{post_id}/pin")
async def pin_post(
    post_id: int,
    req: PinRequest = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "community_director"))
):
    service = TopicOpsService(db)
    duration = req.duration_hours if req else 72
    await service.pin_post(post_id, duration, current_user["id"])

    if request:
        await log_audit(
            request=request,
            action="pin_post",
            target_type="post",
            target_id=post_id,
            detail=f"置顶{duration}小时"
        )

    return {"success": True, "message": f"帖子已置顶{duration}小时"}


@router.delete("/posts/{post_id}/pin")
async def unpin_post(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "community_director"))
):
    service = TopicOpsService(db)
    await service.unpin_post(post_id)

    await log_audit(
        request=request,
        action="unpin_post",
        target_type="post",
        target_id=post_id
    )

    return {"success": True, "message": "帖子已取消置顶"}


@router.post("/posts/{post_id}/feature")
async def feature_post(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "community_director"))
):
    service = TopicOpsService(db)
    await service.feature_post(post_id, current_user["id"])

    await log_audit(
        request=request,
        action="feature_post",
        target_type="post",
        target_id=post_id
    )

    return {"success": True, "message": "帖子已加精"}


@router.delete("/posts/{post_id}/feature")
async def unfeature_post(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "community_director"))
):
    service = TopicOpsService(db)
    await service.unfeature_post(post_id)

    await log_audit(
        request=request,
        action="unfeature_post",
        target_type="post",
        target_id=post_id
    )

    return {"success": True, "message": "帖子已取消加精"}


@router.post("/posts/{post_id}/recommend")
async def recommend_post(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "community_director"))
):
    service = TopicOpsService(db)
    await service.recommend_post(post_id, current_user["id"])

    await log_audit(
        request=request,
        action="recommend_post",
        target_type="post",
        target_id=post_id
    )

    return {"success": True, "message": "帖子已推荐到首页"}


@router.delete("/posts/{post_id}/recommend")
async def unrecommend_post(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "community_director"))
):
    service = TopicOpsService(db)
    await service.unrecommend_post(post_id)

    await log_audit(
        request=request,
        action="unrecommend_post",
        target_type="post",
        target_id=post_id
    )

    return {"success": True, "message": "帖子已取消推荐"}


@router.get("/recommendations")
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "community_director"))
):
    service = TopicOpsService(db)
    slots = await service.get_recommendation_slots()
    return {"success": True, "data": slots}


@router.put("/recommendations")
async def update_recommendations(
    req: SlotsUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "community_director"))
):
    service = TopicOpsService(db)
    slots_data = [s.dict() for s in req.slots]
    await service.update_recommendation_slots(slots_data, current_user["id"])

    await log_audit(
        request=request,
        action="update_recommendations",
        target_type="recommendation_slots",
        detail=f"更新{len(req.slots)}个推荐位"
    )

    return {"success": True, "message": "推荐位已更新"}


@router.put("/{topic_id}/announcement")
async def set_topic_announcement(
    topic_id: int,
    req: AnnouncementRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "community_director"))
):
    service = TopicOpsService(db)
    await service.update_topic_announcement(topic_id, req.content, current_user["id"])

    await log_audit(
        request=request,
        action="set_topic_announcement",
        target_type="topic",
        target_id=topic_id,
        detail=req.content[:100]
    )

    return {"success": True, "message": "话题公告已更新"}
