"""论坛收藏相关路由"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.forum import PostListResponse
from ...services.forum_service import forum_service
from ...utils.deps import get_current_user
from .common import _build_post_response

router = APIRouter()


async def _build_post_responses(db: AsyncSession, posts, user_id: int | None):
    return [await _build_post_response(db, post, user_id) for post in posts]


@router.post("/posts/{post_id}/favorite", summary="收藏/取消收藏帖子")
async def toggle_post_favorite(
    post_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """切换帖子收藏状态"""
    post = await forum_service.get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")

    favorited, favorite_count = await forum_service.toggle_post_favorite(db, post_id, current_user.id)
    message = "收藏成功" if favorited else "取消收藏"

    return {"favorited": favorited,
            "favorite_count": favorite_count, "message": message}


@router.get("/favorites", response_model=PostListResponse, summary="获取我的收藏")
async def get_my_favorites(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
):
    """获取当前用户收藏的帖子列表"""
    posts, total = await forum_service.get_user_favorites(db, current_user.id, page, page_size, category, keyword)

    items = await _build_post_responses(db, posts, current_user.id)

    return PostListResponse(items=items, total=total,
                            page=page, page_size=page_size)
