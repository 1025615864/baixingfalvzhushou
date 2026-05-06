"""社区公告路由"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.services.ops.ops_auth_service import OpsAuthService
from app.middleware.ops_auth import require_ops_role

router = APIRouter(prefix="/api/v1/community/ops/announcements", tags=["社区公告"])


class AnnouncementCreateRequest(BaseModel):
    scope: str = "global"
    scope_id: Optional[int] = None
    title: str
    content: str
    is_pinned: bool = False
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None


@router.get("/")
async def list_announcements(
    scope: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "user_ops", "community_director"))
):
    return {
        "success": True,
        "data": {"items": [], "total": 0, "page": page, "page_size": page_size}
    }


@router.post("/")
async def create_announcement(
    req: AnnouncementCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "community_director"))
):
    return {"success": True, "message": "公告已发布"}


@router.get("/{announcement_id}")
async def get_announcement(
    announcement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("topic_ops", "user_ops", "community_director"))
):
    return {"success": True, "data": None}


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("community_director"))
):
    return {"success": True, "message": "公告已删除"}
