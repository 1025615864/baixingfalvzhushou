"""新闻路由"""
from typing import List, Optional

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel, Field
from datetime import datetime

from app.models import News, NewsCategory, NewsTag, UserNewsInteraction
from app.services.news_service import news_service
from app.database import get_db, AsyncSession

router = APIRouter()


# --- Response Models ---

class CategoryOut(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None


class TagOut(BaseModel):
    id: int
    name: str
    slug: str
    news_count: int = 0


class NewsOut(BaseModel):
    id: int
    title: str
    summary: str
    category_id: int
    cover_image: Optional[str] = None
    view_count: int
    like_count: int
    share_count: int
    published_at: Optional[datetime] = None


class NewsDetailOut(BaseModel):
    id: int
    title: str
    content: str
    summary: str
    category_id: int
    cover_image: Optional[str] = None
    view_count: int
    like_count: int
    share_count: int
    published_at: Optional[datetime] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None


class NewsListResponse(BaseModel):
    items: List[NewsOut]
    total: int
    page: int
    page_size: int


class NewsDetailResponse(BaseModel):
    news: NewsDetailOut
    is_bookmarked: bool = False


class UserBookmarksResponse(BaseModel):
    items: List[NewsOut]
    total: int
    page: int
    page_size: int


# --- 路由 ---

@router.get("/categories", response_model=List[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """获取新闻分类列表"""
    result = await db.execute(
        select(NewsCategory).order_by(NewsCategory.sort_order)
    )
    categories = result.scalars().all()
    return [
        CategoryOut(
            id=c.id,
            name=c.name,
            code=c.code,
            description=c.description,
        )
        for c in categories
    ]


@router.get("/tags", response_model=List[TagOut])
async def list_tags(db: AsyncSession = Depends(get_db)):
    """获取新闻标签列表"""
    result = await db.execute(
        select(NewsTag).order_by(NewsTag.name)
    )
    tags = result.scalars().all()
    return [
        TagOut(
            id=t.id,
            name=t.name,
            slug=t.slug,
            news_count=t.news_count,
        )
        for t in tags
    ]


@router.get("/", response_model=NewsListResponse)
async def list_news(
    category_id: Optional[int] = Query(None, ge=1),
    tag_id: Optional[int] = Query(None, ge=1),
    q: Optional[str] = Query(None, min_length=1, max_length=100),
    sort_by: str = Query("latest", pattern="^(latest|hot)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取新闻列表（支持分类、标签、搜索筛选）"""
    news_list, total = await news_service.get_news_list(
        db,
        category_id=category_id,
        tag_id=tag_id,
        query=q,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
    )

    return NewsListResponse(
        items=[
            NewsOut(
                id=n.id,
                title=n.title,
                summary=n.summary,
                category_id=n.category_id,
                cover_image=n.cover_image,
                view_count=n.view_count,
                like_count=n.like_count,
                share_count=n.share_count,
                published_at=n.published_at,
            )
            for n in news_list
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/category/{category_id}", response_model=NewsListResponse)
async def list_news_by_category(
    category_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取分类下的新闻"""
    news_list, total = await news_service.get_news_by_category(
        db,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )

    return NewsListResponse(
        items=[
            NewsOut(
                id=n.id,
                title=n.title,
                summary=n.summary,
                category_id=n.category_id,
                cover_image=n.cover_image,
                view_count=n.view_count,
                like_count=n.like_count,
                share_count=n.share_count,
                published_at=n.published_at,
            )
            for n in news_list
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{news_id}", response_model=NewsDetailResponse)
async def get_news(
    news_id: int,
    user_id: Optional[int] = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """获取新闻详情"""
    news = await news_service.get_news_detail(db, news_id)
    if not news:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="新闻不存在")

    is_bookmarked = False
    if user_id:
        from sqlalchemy import select
        result = await db.execute(
            select(UserNewsInteraction).where(
                UserNewsInteraction.user_id == user_id,
                UserNewsInteraction.news_id == news_id,
                UserNewsInteraction.is_bookmarked == True,
            )
        )
        interaction = result.scalar_one_or_none()
        is_bookmarked = interaction is not None

    return NewsDetailResponse(
        news=NewsDetailOut(
            id=news.id,
            title=news.title,
            content=news.content,
            summary=news.summary,
            category_id=news.category_id,
            cover_image=news.cover_image,
            view_count=news.view_count,
            like_count=news.like_count,
            share_count=news.share_count,
            published_at=news.published_at,
            source=news.source,
            source_url=news.source_url,
            author=news.author,
        ),
        is_bookmarked=is_bookmarked,
    )


@router.post("/{news_id}/bookmark")
async def bookmark_news(
    news_id: int,
    user_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
):
    """收藏新闻"""
    await news_service.bookmark_news(db, user_id, news_id)
    return {"message": "收藏成功"}


@router.delete("/{news_id}/bookmark")
async def unbookmark_news(
    news_id: int,
    user_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
):
    """取消收藏"""
    await news_service.unbookmark_news(db, user_id, news_id)
    return {"message": "取消收藏成功"}


@router.get("/user/bookmarks", response_model=UserBookmarksResponse)
async def get_user_bookmarks(
    user_id: int = Query(..., ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取用户收藏的新闻"""
    news_list, total = await news_service.get_user_bookmarks(
        db,
        user_id=user_id,
        page=page,
        page_size=page_size,
    )

    return UserBookmarksResponse(
        items=[
            NewsOut(
                id=n.id,
                title=n.title,
                summary=n.summary,
                category_id=n.category_id,
                cover_image=n.cover_image,
                view_count=n.view_count,
                like_count=n.like_count,
                share_count=n.share_count,
                published_at=n.published_at,
            )
            for n in news_list
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/search", response_model=NewsListResponse)
async def search_news(
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """搜索新闻"""
    news_list, total = await news_service.search_news(
        db,
        query=q,
        page=page,
        page_size=page_size,
    )

    return NewsListResponse(
        items=[
            NewsOut(
                id=n.id,
                title=n.title,
                summary=n.summary,
                category_id=n.category_id,
                cover_image=n.cover_image,
                view_count=n.view_count,
                like_count=n.like_count,
                share_count=n.share_count,
                published_at=n.published_at,
            )
            for n in news_list
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
