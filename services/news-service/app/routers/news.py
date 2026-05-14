"""新闻路由"""
from typing import List, Optional

import logging

from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from sqlalchemy import select

from app.models import News, NewsCategory, NewsTag, UserNewsInteraction, NewsTagAssociation, NewsAuditLog
from app.services.news_service import news_service
from app.services.news_admin_service import news_admin_service
from app.database import get_db, AsyncSession
from app.events.kafka_producer import publish_news_published

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_STATUSES = {"draft", "review", "approved", "published", "archived", "rejected"}

VALID_TRANSITIONS = {
    "draft": ["review", "archived"],
    "review": ["approved", "rejected", "draft"],
    "approved": ["published", "review"],
    "published": ["archived"],
    "rejected": ["draft", "review"],
    "archived": ["draft"],
}


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


class NewsCreateRequest(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    category_id: Optional[int] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None
    cover_image: Optional[str] = None
    status: str = "draft"
    tag_ids: Optional[List[int]] = None
    author_id: Optional[int] = None
    author_name: Optional[str] = None


class NewsUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category_id: Optional[int] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = None
    tag_ids: Optional[List[int]] = None
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None


class NewsManageOut(BaseModel):
    id: int
    title: str
    content: str
    summary: Optional[str] = None
    category_id: Optional[int] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    author: Optional[str] = None
    cover_image: Optional[str] = None
    status: str
    view_count: int
    like_count: int
    share_count: int
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


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


@router.post("/manage", response_model=NewsManageOut)
async def create_news(
    body: NewsCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"无效的状态: {body.status}，可选值: {', '.join(VALID_STATUSES)}")

    news = News(
        title=body.title,
        content=body.content,
        summary=body.summary,
        category_id=body.category_id,
        source=body.source,
        source_url=body.source_url,
        author=body.author,
        cover_image=body.cover_image,
        status=body.status,
    )
    if body.status == "published":
        news.published_at = datetime.now(timezone.utc)
    db.add(news)
    await db.flush()
    if body.tag_ids:
        for tag_id in body.tag_ids:
            assoc = NewsTagAssociation(news_id=news.id, tag_id=tag_id)
            db.add(assoc)

    if body.author_id:
        await news_admin_service._create_audit_log(
            db, news.id, body.author_id, body.author_name,
            "create", None, body.status,
            f"创建新闻，状态: {body.status}",
        )

    await db.commit()
    await db.refresh(news)
    return NewsManageOut(
        id=news.id,
        title=news.title,
        content=news.content,
        summary=news.summary,
        category_id=news.category_id,
        source=news.source,
        source_url=news.source_url,
        author=news.author,
        cover_image=news.cover_image,
        status=news.status,
        view_count=news.view_count,
        like_count=news.like_count,
        share_count=news.share_count,
        published_at=news.published_at,
        created_at=news.created_at,
        updated_at=news.updated_at,
    )


@router.put("/manage/{news_id}", response_model=NewsManageOut)
async def update_news(
    news_id: int,
    body: NewsUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")

    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"无效的状态: {body.status}")
        if body.status != news.status:
            allowed = VALID_TRANSITIONS.get(news.status, [])
            if body.status not in allowed:
                raise HTTPException(
                    status_code=400,
                    detail=f"不可从 {news.status} 变更为 {body.status}，允许的转换: {', '.join(allowed) or '无'}",
                )

    from_status = news.status
    update_data = body.model_dump(exclude_unset=True, exclude={"tag_ids", "operator_id", "operator_name"})
    for field, value in update_data.items():
        setattr(news, field, value)
    if body.status == "published" and news.published_at is None:
        news.published_at = datetime.now(timezone.utc)
    if body.tag_ids is not None:
        await db.execute(
            NewsTagAssociation.__table__.delete().where(
                NewsTagAssociation.news_id == news_id
            )
        )
        for tag_id in body.tag_ids:
            assoc = NewsTagAssociation(news_id=news_id, tag_id=tag_id)
            db.add(assoc)

    if body.operator_id and body.status and body.status != from_status:
        await news_admin_service._create_audit_log(
            db, news_id, body.operator_id, body.operator_name,
            f"update_{body.status}", from_status, body.status,
            f"更新新闻状态: {from_status} → {body.status}",
        )

    await db.commit()
    await db.refresh(news)
    return NewsManageOut(
        id=news.id,
        title=news.title,
        content=news.content,
        summary=news.summary,
        category_id=news.category_id,
        source=news.source,
        source_url=news.source_url,
        author=news.author,
        cover_image=news.cover_image,
        status=news.status,
        view_count=news.view_count,
        like_count=news.like_count,
        share_count=news.share_count,
        published_at=news.published_at,
        created_at=news.created_at,
        updated_at=news.updated_at,
    )


@router.delete("/manage/{news_id}")
async def delete_news(
    news_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    await db.delete(news)
    await db.commit()
    return {"message": "删除成功"}


@router.patch("/manage/{news_id}/publish", response_model=NewsManageOut)
async def publish_news(
    news_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")

    if news.status not in ("approved", "published"):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 {news.status} 不可发布，需先通过审核（approved）才能发布",
        )

    from_status = news.status
    news.status = "published"
    if news.published_at is None:
        news.published_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(news)

    try:
        await publish_news_published(
            news_id=str(news_id),
            title=news.title,
            author_id="system",
            category=str(news.category_id or ""),
        )
    except Exception as e:
        logger.error(f"Failed to publish news event: {e}")

    return NewsManageOut(
        id=news.id,
        title=news.title,
        content=news.content,
        summary=news.summary,
        category_id=news.category_id,
        source=news.source,
        source_url=news.source_url,
        author=news.author,
        cover_image=news.cover_image,
        status=news.status,
        view_count=news.view_count,
        like_count=news.like_count,
        share_count=news.share_count,
        published_at=news.published_at,
        created_at=news.created_at,
        updated_at=news.updated_at,
    )


@router.patch("/manage/{news_id}/archive", response_model=NewsManageOut)
async def archive_news(
    news_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")

    if news.status not in ("draft", "published"):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 {news.status} 不可归档，仅草稿或已发布状态可归档",
        )

    news.status = "archived"
    await db.commit()
    await db.refresh(news)
    return NewsManageOut(
        id=news.id,
        title=news.title,
        content=news.content,
        summary=news.summary,
        category_id=news.category_id,
        source=news.source,
        source_url=news.source_url,
        author=news.author,
        cover_image=news.cover_image,
        status=news.status,
        view_count=news.view_count,
        like_count=news.like_count,
        share_count=news.share_count,
        published_at=news.published_at,
        created_at=news.created_at,
        updated_at=news.updated_at,
    )


@router.post("/{news_id}/like")
async def like_news(
    news_id: int,
    user_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    interaction = await news_service._get_or_create_interaction(db, user_id, news_id)
    if not interaction.is_liked:
        interaction.is_liked = True
        news.like_count += 1
    await db.commit()
    return {"message": "点赞成功"}


@router.delete("/{news_id}/like")
async def unlike_news(
    news_id: int,
    user_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserNewsInteraction).where(
            UserNewsInteraction.user_id == user_id,
            UserNewsInteraction.news_id == news_id,
        )
    )
    interaction = result.scalar_one_or_none()
    if interaction and interaction.is_liked:
        interaction.is_liked = False
        result = await db.execute(select(News).where(News.id == news_id))
        news = result.scalar_one_or_none()
        if news:
            news.like_count = max(0, news.like_count - 1)
    await db.commit()
    return {"message": "取消点赞成功"}


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
        raise HTTPException(status_code=404, detail="新闻不存在")

    is_bookmarked = False
    if user_id:
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
    await news_service.bookmark_news(db, user_id, news_id)
    try:
        result = await db.execute(select(News).where(News.id == news_id))
        news = result.scalar_one_or_none()
        if news:
            await publish_news_published(
                news_id=str(news_id),
                title=news.title,
                author_id=str(user_id),
                category=str(news.category_id),
            )
    except Exception as e:
        logger.error(f"Failed to publish bookmark event: {e}")
    return {"message": "收藏成功"}


@router.delete("/{news_id}/bookmark")
async def unbookmark_news(
    news_id: int,
    user_id: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
):
    await news_service.unbookmark_news(db, user_id, news_id)
    try:
        result = await db.execute(select(News).where(News.id == news_id))
        news = result.scalar_one_or_none()
        if news:
            await publish_news_published(
                news_id=str(news_id),
                title=news.title,
                author_id=str(user_id),
                category=str(news.category_id),
            )
    except Exception as e:
        logger.error(f"Failed to publish unbookmark event: {e}")
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


@router.patch("/manage/{news_id}/submit-review", response_model=NewsManageOut)
async def submit_for_review(
    news_id: int,
    operator_id: int = Query(..., ge=1),
    operator_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """提交审核（draft → review）"""
    try:
        news = await news_admin_service.submit_for_review(
            db, news_id, operator_id, operator_name,
        )
        await db.commit()
        await db.refresh(news)
        return NewsManageOut(
            id=news.id,
            title=news.title,
            content=news.content,
            summary=news.summary,
            category_id=news.category_id,
            source=news.source,
            source_url=news.source_url,
            author=news.author,
            cover_image=news.cover_image,
            status=news.status,
            view_count=news.view_count,
            like_count=news.like_count,
            share_count=news.share_count,
            published_at=news.published_at,
            created_at=news.created_at,
            updated_at=news.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflow/info")
async def get_workflow_info():
    """获取新闻发布工作流信息"""
    return {
        "statuses": list(VALID_STATUSES),
        "transitions": VALID_TRANSITIONS,
        "workflow": {
            "draft": "草稿 - 初始状态，编辑中",
            "review": "待审核 - 已提交审核，等待编辑审核",
            "approved": "已通过 - 审核通过，待发布",
            "published": "已发布 - 已正式发布",
            "rejected": "已拒绝 - 审核未通过，需修改后重新提交",
            "archived": "已归档 - 不再展示",
        },
        "description": "标准流程: draft → review → approved → published",
    }
