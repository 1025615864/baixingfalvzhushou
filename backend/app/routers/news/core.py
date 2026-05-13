from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User
from app.models.news import News, NewsComment, NewsSubscription
from app.schemas.forum import PostCreate, NewsToForumPostRequest, NewsToForumPostResponse
from app.services.news import news_service
from app.services.forum.core import forum_service

router = APIRouter(tags=["News Core"], prefix="")


class CommentCreateRequest(BaseModel):
    content: str


class SubscriptionCreateRequest(BaseModel):
    value: str


@router.get("/")
async def list_news(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    category: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    news_list, total = await news_service.get_list(db, page=page, page_size=page_size, category=category, keyword=keyword)
    items = []
    for n in news_list:
        items.append({
            "id": n.id, "title": n.title, "summary": getattr(n, "summary", None),
            "category": n.category, "source": n.source,
            "cover_image": getattr(n, "cover_image", None),
            "view_count": getattr(n, "view_count", 0),
            "is_published": n.is_published, "is_top": getattr(n, "is_top", False),
            "created_at": str(n.created_at) if n.created_at else None,
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{news_id}")
async def get_news(news_id: int, db: AsyncSession = Depends(get_db)):
    news = await news_service.get_by_id(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    await news_service.increment_view(db, news_id)
    return {
        "id": news.id, "title": news.title, "content": news.content,
        "summary": getattr(news, "summary", None),
        "category": news.category, "source": news.source,
        "source_url": getattr(news, "source_url", None),
        "cover_image": getattr(news, "cover_image", None),
        "author": getattr(news, "author", None),
        "view_count": getattr(news, "view_count", 0),
        "is_published": news.is_published, "is_top": getattr(news, "is_top", False),
        "created_at": str(news.created_at) if news.created_at else None,
    }


@router.get("/{news_id}/comments")
async def get_news_comments(
    news_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    news = await news_service.get_by_id(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    conditions = [NewsComment.news_id == news_id, NewsComment.is_deleted.is_(False)]
    count_stmt = select(func.count()).select_from(NewsComment).where(*conditions)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = select(NewsComment).where(*conditions).order_by(NewsComment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    comments = (await db.execute(stmt)).scalars().all()
    items = [{"id": c.id, "content": c.content, "user_id": c.user_id, "created_at": str(c.created_at) if c.created_at else None} for c in comments]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/{news_id}/comments")
async def create_news_comment(
    news_id: int,
    data: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    news = await news_service.get_by_id(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    comment = NewsComment(news_id=news_id, user_id=current_user.id, content=data.content, is_deleted=False)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return {"id": comment.id, "content": comment.content, "user_id": comment.user_id}


@router.delete("/{news_id}/comments/{comment_id}")
async def delete_news_comment(
    news_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NewsComment).where(NewsComment.id == comment_id, NewsComment.news_id == news_id)
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    comment.is_deleted = True
    await db.commit()
    return {"success": True}


@router.post("/{news_id}/favorite")
async def toggle_news_favorite(
    news_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    news = await news_service.get_by_id(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")
    return {"success": True, "favorited": True}


@router.get("/subscriptions")
async def get_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NewsSubscription).where(NewsSubscription.user_id == current_user.id)
    result = await db.execute(stmt)
    subs = result.scalars().all()
    return [{"category": s.category, "created_at": str(s.created_at) if s.created_at else None} for s in subs]


@router.post("/subscriptions")
async def create_subscription(
    data: SubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NewsSubscription).where(NewsSubscription.user_id == current_user.id, NewsSubscription.category == data.value)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if not existing:
        sub = NewsSubscription(user_id=current_user.id, category=data.value)
        db.add(sub)
        await db.commit()
    return {"success": True}


@router.delete("/subscriptions/{category}")
async def delete_subscription(
    category: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NewsSubscription).where(NewsSubscription.user_id == current_user.id, NewsSubscription.category == category)
    result = await db.execute(stmt)
    sub = result.scalar_one_or_none()
    if sub:
        await db.delete(sub)
        await db.commit()
    return {"success": True}


@router.get("/subscriptions/feed")
async def get_subscription_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub_stmt = select(NewsSubscription.category).where(NewsSubscription.user_id == current_user.id)
    sub_result = await db.execute(sub_stmt)
    categories = [row[0] for row in sub_result.all()]
    if not categories:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}
    conditions = [News.is_published.is_(True), News.category.in_(categories)]
    count_stmt = select(func.count()).select_from(News).where(*conditions)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = select(News).where(*conditions).order_by(News.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    news_list = (await db.execute(stmt)).scalars().all()
    items = [{"id": n.id, "title": n.title, "category": n.category, "created_at": str(n.created_at) if n.created_at else None} for n in news_list]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/to-forum")
async def news_to_forum(
    data: NewsToForumPostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await news_to_forum_post(data=data, current_user=current_user, db=db)


async def news_to_forum_post(
    data: NewsToForumPostRequest,
    current_user,
    db: AsyncSession,
):
    news = await news_service.get_published(db, news_id=data.news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在")

    title = data.title or f"讨论：{news.title}"
    content = data.content
    if not content:
        parts = []
        if getattr(news, "summary", None):
            parts.append(news.summary)
        if getattr(news, "source_url", None):
            parts.append(f"来源新闻：{news.source_url}")
        content = "\n\n".join(parts) if parts else news.title
    else:
        if getattr(news, "source_url", None):
            content += f"\n\n来源新闻：{news.source_url}"

    post_data = PostCreate(
        title=title,
        content=content,
        category=data.category,
        cover_image=getattr(news, "cover_image", None),
    )

    post = await forum_service.create_post(db=db, user_id=current_user.id, post_data=post_data)

    return NewsToForumPostResponse(
        post_id=post.id,
        post_title=post.title,
        post_url=f"/forum/post/{post.id}",
        message="已成功将新闻转发到论坛讨论",
    )
