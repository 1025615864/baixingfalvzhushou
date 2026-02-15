"""论坛内容审核与管理员接口"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.forum import EssencePostRequest, HotPostRequest, PinPostRequest, PostListResponse
from ...services.forum_service import forum_service
from ...utils.deps import require_admin
from .common import _build_post_response

router = APIRouter()


@router.get("/stats", summary="获取论坛统计")
async def get_forum_stats(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stats = await forum_service.get_forum_stats(db)
    return stats


@router.get("/admin/posts", response_model=PostListResponse,
            summary="管理员获取帖子列表")
async def admin_get_posts(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
    deleted: bool = False,
    is_essence: Annotated[bool | None, Query(description="是否仅精华帖")] = None,
):
    posts, total = await forum_service.get_posts(
        db,
        page,
        page_size,
        category,
        keyword,
        is_essence=is_essence,
        include_deleted=True,
        deleted=deleted,
        approved_only=False,
    )
    items = [await _build_post_response(db, post, current_user.id) for post in posts]
    return PostListResponse(items=items, total=total,
                            page=page, page_size=page_size)


@router.post("/admin/posts/{post_id}/pin", summary="设置置顶")
async def admin_toggle_pin(
    post_id: int,
    pin_data: PinPostRequest,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    success = await forum_service.set_post_pinned(db, post_id, pin_data.is_pinned)
    if not success:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {"message": "置顶成功" if pin_data.is_pinned else "取消置顶成功"}


@router.post("/admin/posts/{post_id}/hot", summary="设置热门")
async def admin_toggle_hot(
    post_id: int,
    hot_data: HotPostRequest,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    success = await forum_service.set_post_hot(db, post_id, hot_data.is_hot)
    if not success:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {"message": "设为热门成功" if hot_data.is_hot else "取消热门成功"}


@router.post("/admin/posts/{post_id}/essence", summary="设置精华")
async def admin_toggle_essence(
    post_id: int,
    essence_data: EssencePostRequest,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    success = await forum_service.set_post_essence(db, post_id, essence_data.is_essence)
    if not success:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {"message": "设为精华成功" if essence_data.is_essence else "取消精华成功"}


@router.post("/admin/update-heat-scores", summary="更新所有帖子热度")
async def admin_update_heat_scores(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    updated = await forum_service.update_heat_scores(db)
    return {"message": f"已更新 {updated} 个帖子的热度分数", "updated_count": updated}
