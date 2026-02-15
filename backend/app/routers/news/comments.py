"""News comments routes

Provides news comment CRUD endpoints
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...schemas.news import (
    NewsCommentCreate, NewsCommentResponse, NewsCommentListResponse,
)
from ...services.news_service import news_service
from ...utils.deps import get_current_user, get_current_user_optional
from ...utils.content_filter import check_comment_content, needs_review

router = APIRouter(prefix="", tags=["News Comments"])


@router.get("/{news_id}/comments",
            response_model=NewsCommentListResponse,
            summary="Get news comments")
async def get_news_comments(
    news_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Get comments for a news article"""
    news = await news_service.get_published(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found")

    comments, total = await news_service.get_comments(db, news_id, page, page_size)
    items = [NewsCommentResponse.model_validate(c) for c in comments]
    return NewsCommentListResponse(
        items=items, total=total, page=page, page_size=page_size)


@router.post("/{news_id}/comments",
             response_model=NewsCommentResponse, summary="Post a comment")
async def create_news_comment(
    news_id: int,
    data: NewsCommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Post a comment on a news article"""
    news = await news_service.get_published(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found")

    # Content filter check
    if not check_comment_content(data.content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content not allowed")

    comment = await news_service.create_comment(db, news_id, int(current_user.id), data.content)
    return NewsCommentResponse.model_validate(comment)


@router.delete("/{news_id}/comments/{comment_id}", summary="Delete a comment")
async def delete_news_comment(
    news_id: int,
    comment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a comment (owner or admin only)"""
    comment = await news_service.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found")
    if comment.user_id != int(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied")
    await news_service.delete_comment(db, comment)
    return {"message": "Comment deleted successfully"}


# 兼容前端路由：DELETE /news/comments/{comment_id}
@router.delete("/comments/{comment_id}", summary="Delete a comment by ID only")
async def delete_news_comment_by_id(
    comment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a comment by comment_id only (owner or admin only)"""
    comment = await news_service.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found")
    if comment.user_id != int(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied")
    await news_service.delete_comment(db, comment)
    return {"message": "Comment deleted successfully"}
