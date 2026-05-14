"""评论路由"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import logging

from ..database import get_db
from ..models import NewsComment
from ..services.comment_service import comment_service
from ..events.kafka_producer import publish_comment_added

logger = logging.getLogger(__name__)

router = APIRouter()


class CommentResponse(BaseModel):
    id: int
    news_id: int
    user_id: int
    content: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    items: List[CommentResponse]
    total: int
    page: int
    page_size: int


class CommentCreateRequest(BaseModel):
    content: str
    user_id: int


@router.get("/{news_id}/comments", response_model=CommentListResponse)
async def list_comments(
    news_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = "approved",
    db: AsyncSession = Depends(get_db)
):
    """获取新闻评论列表"""
    comments, total = await comment_service.list_comments(db, news_id, page, page_size, status)
    return CommentListResponse(
        items=[CommentResponse.model_validate(c) for c in comments],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/{news_id}/comments", response_model=CommentResponse)
async def create_comment(
    news_id: int,
    request: CommentCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建评论"""
    comment = await comment_service.create_comment(db, news_id, request.user_id, request.content)
    await db.commit()
    await db.refresh(comment)
    try:
        await publish_comment_added(
            news_id=str(news_id),
            comment_id=str(comment.id),
            user_id=str(request.user_id),
            content=request.content,
        )
    except Exception as e:
        logger.error(f"Failed to publish comment event: {e}")
    return CommentResponse.model_validate(comment)


@router.patch("/{comment_id}/approve")
async def approve_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    """审核通过评论"""
    try:
        await comment_service.approve_comment(db, comment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Comment not found")
    await db.commit()
    return {"success": True}


@router.patch("/{comment_id}/reject")
async def reject_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    """审核拒绝评论"""
    try:
        await comment_service.reject_comment(db, comment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Comment not found")
    await db.commit()
    return {"success": True}


@router.delete("/{comment_id}")
async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    """删除评论"""
    try:
        await comment_service.delete_comment(db, comment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Comment not found")
    await db.commit()
    return {"success": True}
