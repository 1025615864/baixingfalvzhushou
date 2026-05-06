"""热门内容路由"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services import HotService
from ..schemas import PostListResponse, PostResponse

router = APIRouter()


async def get_hot_service(db: AsyncSession = Depends(get_db)) -> HotService:
    return HotService(db)


@router.get("/posts", response_model=PostListResponse)
async def get_hot_posts(
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    service: HotService = Depends(get_hot_service)
):
    posts = await service.get_hot_posts(category=category, limit=limit)
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=len(posts),
        page=1,
        page_size=limit
    )


@router.post("/recalculate")
async def recalculate_hot_scores(
    post_ids: Optional[list[int]] = None,
    service: HotService = Depends(get_hot_service)
):
    await service.update_hot_scores(post_ids)
    return {"success": True, "message": "热度分数已更新"}
