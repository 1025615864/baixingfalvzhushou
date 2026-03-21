"""帖子路由"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..database import get_db
from ..models import Post

router = APIRouter()


class PostResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    category: Optional[str] = None
    status: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    items: List[PostResponse]
    total: int
    page: int
    page_size: int


class PostCreateRequest(BaseModel):
    user_id: int
    title: str
    content: str
    category: Optional[str] = "general"


class PostUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


@router.get("/", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取帖子列表"""
    query = select(Post).where(Post.status == "published")
    
    if category:
        query = query.where(Post.category == category)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(desc(Post.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """获取帖子详情"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.view_count += 1
    await db.commit()
    
    return PostResponse.model_validate(post)


@router.post("/", response_model=PostResponse)
async def create_post(
    request: PostCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建帖子"""
    post = Post(
        user_id=request.user_id,
        title=request.title,
        content=request.content,
        category=request.category,
        status="published",
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    
    return PostResponse.model_validate(post)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    request: PostUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新帖子"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if request.title is not None:
        post.title = request.title
    if request.content is not None:
        post.content = request.content
    if request.category is not None:
        post.category = request.category
    
    await db.commit()
    await db.refresh(post)
    
    return PostResponse.model_validate(post)


@router.delete("/{post_id}")
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """删除帖子"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.status = "deleted"
    await db.commit()
    
    return {"success": True}


@router.post("/{post_id}/like")
async def like_post(post_id: int, db: AsyncSession = Depends(get_db)):
    """点赞帖子"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.like_count += 1
    await db.commit()
    
    return {"success": True, "like_count": post.like_count}


@router.get("/categories/", response_model=List[str])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """获取所有分类"""
    result = await db.execute(
        select(Post.category)
        .where(Post.status == "published")
        .distinct()
    )
    categories = result.scalars().all()
    return list(categories)
