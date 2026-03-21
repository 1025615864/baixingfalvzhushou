"""评论路由"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..database import get_db
from ..models import Comment

router = APIRouter()


class CommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    parent_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    items: List[CommentResponse]
    total: int
    page: int
    page_size: int


class CommentCreateRequest(BaseModel):
    user_id: int
    content: str
    parent_id: int | None = None


@router.get("/{post_id}/comments", response_model=CommentListResponse)
async def list_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取帖子评论列表"""
    query = select(Comment).where(Comment.post_id == post_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(desc(Comment.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    comments = result.scalars().all()
    
    return CommentListResponse(
        items=[CommentResponse.model_validate(c) for c in comments],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    request: CommentCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建评论"""
    comment = Comment(
        post_id=post_id,
        user_id=request.user_id,
        content=request.content,
        parent_id=request.parent_id,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    return CommentResponse.model_validate(comment)


@router.delete("/{comment_id}")
async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db)):
    """删除评论"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    await db.delete(comment)
    await db.commit()
    
    return {"success": True}
