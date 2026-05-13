from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User
from app.models.forum import Post, PostFavorite
from app.services.forum.core import ForumService

router = APIRouter(tags=["Forum Favorites"])

forum_service = ForumService()


async def _build_post_responses(db: AsyncSession, posts, user_id: int = None) -> list[dict]:
    return []


@router.post("/posts/{post_id}/favorite")
async def toggle_favorite(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    post = await forum_service.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    favorited, count = await forum_service.toggle_post_favorite(db, post_id=post_id, user_id=current_user.id)
    if favorited:
        return {"favorited": favorited, "favorite_count": count, "message": "收藏成功"}
    else:
        return {"favorited": favorited, "favorite_count": count, "message": "取消收藏"}


@router.get("/favorites")
async def list_favorites(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    category: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    favorites, total = await forum_service.get_user_favorites(db, user_id=current_user.id, page=page, page_size=page_size, category=category, keyword=keyword)
    post_ids = [f.post_id for f in favorites]
    posts = []
    if post_ids:
        stmt = select(Post).where(Post.id.in_(post_ids))
        result = await db.execute(stmt)
        posts = result.scalars().all()
    items = await _build_post_responses(db, posts, user_id=current_user.id)
    return {"items": items, "total": total, "page": page, "page_size": page_size}
