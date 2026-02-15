"""论坛表情反应路由"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.forum import ReactionCount, ReactionRequest, ReactionResponse
from ...services.forum_service import forum_service
from ...utils.deps import get_current_user

router = APIRouter()


@router.post("/posts/{post_id}/reaction",
             response_model=ReactionResponse, summary="添加/取消表情反应")
async def toggle_reaction(
    post_id: int,
    reaction_data: ReactionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """添加或取消帖子的表情反应"""
    post = await forum_service.get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")

    reacted, _ = await forum_service.toggle_reaction(db, post_id, current_user.id, reaction_data.emoji)
    reactions = await forum_service.get_post_reactions(db, post_id)

    return ReactionResponse(
        reacted=reacted,
        emoji=reaction_data.emoji,
        reactions=[
            ReactionCount(
                emoji=str(
                    r["type"]), count=int(
                    r["count"])) for r in reactions],
        message="已添加反应" if reacted else "已取消反应",
    )
