from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User
from app.models.forum import Post
from app.services.forum.core import ForumService

router = APIRouter(tags=["Forum Reactions"])

forum_service = ForumService()


class ReactionRequest(BaseModel):
    emoji: str = "👍"


@router.post("/posts/{post_id}/reaction")
async def toggle_reaction(
    post_id: int,
    data: ReactionRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    emoji = data.emoji if data else "👍"
    post = await forum_service.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    reacted, reactions = await forum_service.toggle_reaction(db, post_id=post_id, user_id=current_user.id, emoji=emoji)
    if isinstance(reactions, int):
        reactions_list = await forum_service.get_post_reactions(db, post_id)
    else:
        reactions_list = reactions
    if reacted:
        return {"reacted": reacted, "emoji": emoji, "message": "已添加反应", "reactions": reactions_list}
    else:
        return {"reacted": reacted, "emoji": emoji, "message": "已取消反应", "reactions": reactions_list}


@router.get("/posts/{post_id}/reactions")
async def get_reactions(post_id: int, db: AsyncSession = Depends(get_db)):
    reactions = await forum_service.get_post_reactions(db, post_id=post_id)
    return {"reactions": reactions}


@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Post).where(Post.id == post_id, Post.is_deleted.is_(False))
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    liked, count = await forum_service.toggle_post_like(db, post_id=post_id, user_id=current_user.id)
    return {"liked": liked, "like_count": count}
