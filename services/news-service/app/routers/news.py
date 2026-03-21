"""新闻路由"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..database import get_db
from ..models import News, NewsComment

router = APIRouter()


class NewsResponse(BaseModel):
    id: int
    title: str
    content: str
    summary: Optional[str] = None
    category: str
    tags: List[str] = []
    author: Optional[str] = None
    cover_image: Optional[str] = None
    status: str
    view_count: int = 0
    like_count: int = 0
    published_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    items: List[NewsResponse]
    total: int
    page: int
    page_size: int


class NewsCreateRequest(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    category: str = "general"
    tags: List[str] = []
    author: Optional[str] = None
    cover_image: Optional[str] = None


class CommentResponse(BaseModel):
    id: int
    news_id: int
    user_id: int
    content: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CommentCreateRequest(BaseModel):
    content: str
    user_id: int


@router.get("/", response_model=NewsListResponse)
async def list_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    status: str = "published",
    db: AsyncSession = Depends(get_db)
):
    """获取新闻列表"""
    query = select(News).where(News.status == status)
    
    if category:
        query = query.where(News.category == category)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(desc(News.published_at), desc(News.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    news_list = result.scalars().all()
    
    items = []
    for news in news_list:
        items.append(NewsResponse(
            id=news.id,
            title=news.title,
            content=news.content,
            summary=news.summary,
            category=news.category,
            tags=news.tags or [],
            author=news.author,
            cover_image=news.cover_image,
            status=news.status,
            view_count=news.view_count or 0,
            like_count=news.like_count or 0,
            published_at=news.published_at,
            created_at=news.created_at,
        ))
    
    return NewsListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news(news_id: int, db: AsyncSession = Depends(get_db)):
    """获取新闻详情"""
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    return NewsResponse.model_validate(news)


@router.post("/", response_model=NewsResponse)
async def create_news(
    request: NewsCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建新闻"""
    news = News(
        title=request.title,
        content=request.content,
        summary=request.summary,
        category=request.category,
        tags=request.tags,
        author=request.author,
        cover_image=request.cover_image,
        status="draft",
    )
    db.add(news)
    await db.commit()
    await db.refresh(news)
    
    return NewsResponse.model_validate(news)


@router.patch("/{news_id}/publish")
async def publish_news(news_id: int, db: AsyncSession = Depends(get_db)):
    """发布新闻"""
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    news.status = "published"
    news.published_at = datetime.utcnow()
    await db.commit()
    
    return {"success": True}


@router.delete("/{news_id}")
async def delete_news(news_id: int, db: AsyncSession = Depends(get_db)):
    """删除新闻"""
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    await db.delete(news)
    await db.commit()
    
    return {"success": True}


@router.get("/categories/", response_model=List[str])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """获取所有分类"""
    result = await db.execute(
        select(News.category)
        .where(News.status == "published")
        .distinct()
    )
    categories = result.scalars().all()
    return list(categories)
