"""News core routes

Provides news CRUD, list, detail, favorite and other core functions
"""
import json
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...database import get_db
from ...models.news import News
from ...models.news_ai import NewsAIAnnotation
from ...models.user import User
from ...schemas.news import (
    NewsListResponse, NewsListItem, NewsResponse, NewsFavoriteResponse,
    NewsAIAnnotationResponse, NewsCategoryCount,
)
from ...schemas.forum import PostCreate, NewsToForumPostRequest, NewsToForumPostResponse
from ...services.news_service import news_service
from ...services.forum_service import forum_service
from ...utils.deps import get_current_user, get_current_user_optional
from ...utils.helpers import _parse_dt_param

router = APIRouter(prefix="/news", tags=["News"])


async def _get_ai_risk_levels(
        db: AsyncSession, news_ids: list[int]) -> dict[int, str]:
    """Get AI risk levels for news items"""
    ids = [int(i) for i in news_ids]
    if not ids:
        return {}

    res = await db.execute(
        select(NewsAIAnnotation.news_id, NewsAIAnnotation.risk_level).where(
            NewsAIAnnotation.news_id.in_(ids)
        )
    )
    rows = cast(list[tuple[object, object]], list(res.all()))
    out: dict[int, str] = {}
    for news_id_obj, risk_level_obj in rows:
        nid = 0
        if isinstance(news_id_obj, int):
            nid = int(news_id_obj)
        elif isinstance(news_id_obj, float):
            nid = int(news_id_obj)
        elif isinstance(news_id_obj, str):
            s = news_id_obj.strip()
            if s.isdigit():
                nid = int(s)
        if nid <= 0:
            continue
        out[int(nid)] = str(risk_level_obj or "unknown")
    return out


async def _get_ai_keywords(
        db: AsyncSession, news_ids: list[int]) -> dict[int, list[str]]:
    """Get AI keywords for news items"""
    ids = [int(i) for i in news_ids]
    if not ids:
        return {}

    res = await db.execute(
        select(NewsAIAnnotation.news_id, NewsAIAnnotation.keywords).where(
            NewsAIAnnotation.news_id.in_(ids)
        )
    )
    rows = cast(list[tuple[object, object]], list(res.all()))
    out: dict[int, list[str]] = {}
    for news_id_obj, raw in rows:
        nid = 0
        if isinstance(news_id_obj, int):
            nid = int(news_id_obj)
        elif isinstance(news_id_obj, float):
            nid = int(news_id_obj)
        elif isinstance(news_id_obj, str):
            s = news_id_obj.strip()
            if s.isdigit():
                nid = int(s)
        if nid <= 0:
            continue

        kws: list[str] = []
        try:
            if isinstance(raw, str) and raw.strip():
                parsed: object = cast(object, json.loads(raw))
                if isinstance(parsed, list):
                    for x in cast(list[object], parsed):
                        s = str(x or "").strip()
                        if s:
                            kws.append(s)
        except Exception:
            logger.exception("Failed to parse keywords JSON")
            kws = []
        out[int(nid)] = kws
    return out


def _build_news_list_items(
    news_list: list[News],
    fav_stats: dict[int, tuple[int, bool]],
    risk_levels: dict[int, str],
    keywords_map: dict[int, list[str]],
    user_id: int | None,
) -> list[NewsListItem]:
    """Build NewsListItem list from news list"""
    items: list[NewsListItem] = []
    for news in news_list:
        item = NewsListItem.model_validate(news)
        fav_count, is_fav = fav_stats.get(int(news.id), (0, False))
        item.favorite_count = int(fav_count)
        item.is_favorited = bool(is_fav)
        item.ai_risk_level = risk_levels.get(int(news.id))
        item.ai_keywords = keywords_map.get(int(news.id), [])
        items.append(item)
    return items


@router.get("", response_model=NewsListResponse, summary="Get news list")
async def get_news_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
    risk_level: str | None = None,
    source_site: str | None = None,
    from_dt: Annotated[str | None, Query(alias="from")] = None,
    to_dt: Annotated[str | None, Query(alias="to")] = None,
):
    """Get news list with category filter and keyword search"""
    parsed_from = _parse_dt_param(from_dt, field="from")
    parsed_to = _parse_dt_param(to_dt, field="to", end_of_day=True)
    news_list, total = await news_service.get_list(
        db, page, page_size, category, keyword,
        published_only=True,
        ai_risk_level=risk_level,
        source_site=source_site,
        from_dt=parsed_from,
        to_dt=parsed_to,
    )

    ids = [int(n.id) for n in news_list]
    user_id = current_user.id if current_user else None
    fav_stats = await news_service.get_favorite_stats(db, ids, int(user_id) if user_id is not None else None)
    risk_levels = await _get_ai_risk_levels(db, ids)
    keywords_map = await _get_ai_keywords(db, ids)

    items = _build_news_list_items(
        news_list,
        fav_stats,
        risk_levels,
        keywords_map,
        user_id)
    return NewsListResponse(items=items, total=total,
                            page=page, page_size=page_size)


@router.get("/recommended", response_model=NewsListResponse,
            summary="Get recommended news")
async def get_recommended_news(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
    risk_level: str | None = None,
    source_site: str | None = None,
    from_dt: Annotated[str | None, Query(alias="from")] = None,
    to_dt: Annotated[str | None, Query(alias="to")] = None,
):
    """Get recommended news list"""
    parsed_from = _parse_dt_param(from_dt, field="from")
    parsed_to = _parse_dt_param(to_dt, field="to", end_of_day=True)
    user_id = current_user.id if current_user else None

    news_list, total = await news_service.get_recommended_news(
        db,
        int(user_id) if user_id is not None else None,
        page=page,
        page_size=page_size,
        category=category,
        keyword=keyword,
        ai_risk_level=risk_level,
        source_site=source_site,
        from_dt=parsed_from,
        to_dt=parsed_to,
    )

    ids = [int(n.id) for n in news_list]
    fav_stats = await news_service.get_favorite_stats(db, ids, int(user_id) if user_id is not None else None)
    risk_levels = await _get_ai_risk_levels(db, ids)
    keywords_map = await _get_ai_keywords(db, ids)

    items = _build_news_list_items(
        news_list,
        fav_stats,
        risk_levels,
        keywords_map,
        user_id)
    return NewsListResponse(items=items, total=total,
                            page=page, page_size=page_size)


@router.get("/hot", response_model=list[NewsListItem], summary="Get hot news")
async def get_hot_news(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    days: Annotated[int, Query(ge=1, le=365)] = 7,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    category: str | None = None,
):
    """Get hot news within specified days"""
    news_list = await news_service.get_hot_news(db, days=days, limit=limit, category=category)

    ids = [int(n.id) for n in news_list]
    user_id = current_user.id if current_user else None
    fav_stats = await news_service.get_favorite_stats(db, ids, int(user_id) if user_id is not None else None)
    risk_levels = await _get_ai_risk_levels(db, ids)
    keywords_map = await _get_ai_keywords(db, ids)

    items = _build_news_list_items(
        news_list,
        fav_stats,
        risk_levels,
        keywords_map,
        user_id)
    return items


@router.get("/top", response_model=list[NewsListItem], summary="Get top news")
async def get_top_news(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
):
    """Get top/pinned news"""
    news_list = await news_service.get_top_news(db, limit)

    ids = [int(n.id) for n in news_list]
    user_id = current_user.id if current_user else None
    fav_stats = await news_service.get_favorite_stats(db, ids, int(user_id) if user_id is not None else None)
    risk_levels = await _get_ai_risk_levels(db, ids)
    keywords_map = await _get_ai_keywords(db, ids)

    items = _build_news_list_items(
        news_list,
        fav_stats,
        risk_levels,
        keywords_map,
        user_id)
    return items


@router.get("/recent",
            response_model=list[NewsListItem], summary="Get recent news")
async def get_recent_news(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    """Get most recent news"""
    news_list = await news_service.get_recent_news(db, limit)

    ids = [int(n.id) for n in news_list]
    user_id = current_user.id if current_user else None
    fav_stats = await news_service.get_favorite_stats(db, ids, int(user_id) if user_id is not None else None)
    risk_levels = await _get_ai_risk_levels(db, ids)
    keywords_map = await _get_ai_keywords(db, ids)

    items = _build_news_list_items(
        news_list,
        fav_stats,
        risk_levels,
        keywords_map,
        user_id)
    return items


@router.get("/categories",
            response_model=list[NewsCategoryCount],
            summary="Get news categories")
async def get_categories(db: Annotated[AsyncSession, Depends(get_db)]):
    """Get news categories with counts"""
    categories = await news_service.get_categories(db)
    return [
        NewsCategoryCount(
            category=str(cat.get("category", "")),
            count=int(str(cat.get("count", 0) or 0)),
        )
        for cat in categories
    ]


@router.get("/{news_id:int}", response_model=NewsResponse,
            summary="Get news detail")
async def get_news_detail(
    news_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
):
    """Get news detail, automatically increments view count"""
    news = await news_service.get_published(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found")

    await news_service.increment_view(db, news)
    await db.refresh(news)

    if current_user is not None:
        await news_service.record_view_history(db, news.id, current_user.id)

    user_id = current_user.id if current_user is not None else None
    fav_stats = await news_service.get_favorite_stats(db, [int(news.id)], int(user_id) if user_id is not None else None)
    fav_count, is_fav = fav_stats.get(int(news.id), (0, False))
    resp = NewsResponse.model_validate(news)
    resp.favorite_count = int(fav_count)
    resp.is_favorited = bool(is_fav)

    ann_res = await db.execute(select(NewsAIAnnotation).where(NewsAIAnnotation.news_id == int(news.id)))
    ann = ann_res.scalar_one_or_none()
    if ann is not None:
        raw_words = str(getattr(ann, "sensitive_words", "") or "").strip()
        words = [w.strip() for w in raw_words.split(
            ",") if w.strip()] if raw_words else []

        highlights: list[str] = []
        try:
            raw_hl = getattr(ann, "highlights", None)
            parsed_hl: object = cast(
                object, json.loads(raw_hl)) if isinstance(
                raw_hl, str) and raw_hl.strip() else []
            if isinstance(parsed_hl, list):
                for x in cast(list[object], parsed_hl):
                    s = str(x or "").strip()
                    if s:
                        highlights.append(s)
        except Exception:
            logger.exception("Failed to parse highlights JSON")
            highlights = []

        keywords: list[str] = []
        try:
            raw_kw = getattr(ann, "keywords", None)
            parsed_kw: object = cast(
                object, json.loads(raw_kw)) if isinstance(
                raw_kw, str) and raw_kw.strip() else []
            if isinstance(parsed_kw, list):
                for x in cast(list[object], parsed_kw):
                    s = str(x or "").strip()
                    if s:
                        keywords.append(s)
        except Exception:
            logger.exception("Failed to parse keywords JSON")
            keywords = []
        resp.ai_annotation = NewsAIAnnotationResponse(
            summary=getattr(ann, "summary", None),
            risk_level=str(getattr(ann, "risk_level", "unknown") or "unknown"),
            sensitive_words=words,
            highlights=highlights,
            keywords=keywords,
            duplicate_of_news_id=getattr(ann, "duplicate_of_news_id", None),
            processed_at=getattr(ann, "processed_at", None),
        )
    return resp


@router.get("/{news_id:int}/related",
            response_model=list[NewsListItem], summary="Get related news")
async def get_related_news(
    news_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    limit: Annotated[int, Query(ge=1, le=20)] = 6,
):
    """Get related news (same category, excluding current)"""
    news_list = await news_service.get_related_news(db, news_id, limit)

    ids = [int(n.id) for n in news_list]
    user_id = current_user.id if current_user else None
    fav_stats = await news_service.get_favorite_stats(db, ids, int(user_id) if user_id is not None else None)
    risk_levels = await _get_ai_risk_levels(db, ids)
    keywords_map = await _get_ai_keywords(db, ids)

    items = _build_news_list_items(
        news_list,
        fav_stats,
        risk_levels,
        keywords_map,
        user_id)
    return items


@router.post("/{news_id:int}/favorite",
             response_model=NewsFavoriteResponse, summary="Toggle favorite")
async def toggle_news_favorite(
    news_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Toggle favorite status for a news article"""
    news = await news_service.get_published(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found")

    favorited, favorite_count = await news_service.toggle_favorite(db, news_id, current_user.id)
    message = "收藏成功" if favorited else "取消收藏"
    return NewsFavoriteResponse(
        favorited=favorited, favorite_count=favorite_count, message=message)


@router.get("/favorites", response_model=NewsListResponse,
            summary="Get my favorites")
async def get_my_news_favorites(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
    risk_level: str | None = None,
    source_site: str | None = None,
    from_dt: Annotated[str | None, Query(alias="from")] = None,
    to_dt: Annotated[str | None, Query(alias="to")] = None,
):
    """Get user's favorite news list"""
    parsed_from = _parse_dt_param(from_dt, field="from")
    parsed_to = _parse_dt_param(to_dt, field="to", end_of_day=True)
    news_list, total = await news_service.get_user_favorites(  # pyright: ignore
        db, current_user.id, page, page_size,  # pyright: ignore
        category, keyword,  # pyright: ignore
        ai_risk_level=risk_level,
        source_site=source_site,
        from_dt=parsed_from,
        to_dt=parsed_to,
    )  # pyright: ignore

    ids = [int(n.id) for n in news_list]  # pyright: ignore
    fav_stats = await news_service.get_favorite_stats(db, ids, int(current_user.id))
    risk_levels = await _get_ai_risk_levels(db, ids)
    keywords_map = await _get_ai_keywords(db, ids)

    items = _build_news_list_items(
        news_list,
        fav_stats,
        risk_levels,
        keywords_map,
        current_user.id)  # pyright: ignore
    return NewsListResponse(items=items, total=total,
                            page=page, page_size=page_size)  # pyright: ignore


@router.get("/subscribed", response_model=NewsListResponse,
            summary="Get subscribed news")
async def get_my_subscribed_news(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
    risk_level: str | None = None,
    source_site: str | None = None,
    from_dt: Annotated[str | None, Query(alias="from")] = None,
    to_dt: Annotated[str | None, Query(alias="to")] = None,
):
    """Get subscribed news list"""
    parsed_from = _parse_dt_param(from_dt, field="from")
    parsed_to = _parse_dt_param(to_dt, field="to", end_of_day=True)
    news_list, total = await news_service.get_subscribed_news(
        db,
        current_user.id,
        page=page,
        page_size=page_size,
        category=category,
        keyword=keyword,
        ai_risk_level=risk_level,
        source_site=source_site,
        from_dt=parsed_from,
        to_dt=parsed_to,
    )

    ids = [int(n.id) for n in news_list]
    fav_stats = await news_service.get_favorite_stats(db, ids, int(current_user.id))
    risk_levels = await _get_ai_risk_levels(db, ids)
    keywords_map = await _get_ai_keywords(db, ids)

    items = _build_news_list_items(
        news_list,
        fav_stats,
        risk_levels,
        keywords_map,
        current_user.id)
    return NewsListResponse(items=items, total=total,
                            page=page, page_size=page_size)


@router.get("/history", response_model=NewsListResponse,
            summary="Get my browsing history")
async def get_my_news_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
    risk_level: str | None = None,
    source_site: str | None = None,
    from_dt: Annotated[str | None, Query(alias="from")] = None,
    to_dt: Annotated[str | None, Query(alias="to")] = None,
):
    """Get user's browsing history"""
    parsed_from = _parse_dt_param(from_dt, field="from")
    parsed_to = _parse_dt_param(to_dt, field="to", end_of_day=True)
    news_list, total = await news_service.get_user_history(  # pyright: ignore
        db, current_user.id, page, page_size,  # pyright: ignore
        category, keyword,  # pyright: ignore
        ai_risk_level=risk_level,
        source_site=source_site,
        from_dt=parsed_from,
        to_dt=parsed_to,
    )  # pyright: ignore

    ids = [int(n.id) for n in news_list]  # pyright: ignore
    fav_stats = await news_service.get_favorite_stats(db, ids, int(current_user.id))
    risk_levels = await _get_ai_risk_levels(db, ids)
    keywords_map = await _get_ai_keywords(db, ids)

    items = _build_news_list_items(
        news_list,
        fav_stats,
        risk_levels,
        keywords_map,
        current_user.id)  # pyright: ignore
    return NewsListResponse(items=items, total=total,
                            page=page, page_size=page_size)  # pyright: ignore


@router.post("/to-forum", response_model=NewsToForumPostResponse,
             summary="新闻转论坛讨论")
async def news_to_forum_post(
    data: NewsToForumPostRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """将新闻转发到论坛发起讨论（需登录）"""
    news = await news_service.get_published(db, data.news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在")

    title = data.title or f"讨论：{news.title}"
    content_parts: list[str] = []
    if data.content:
        content_parts.append(data.content)
    else:
        if news.summary:
            content_parts.append(news.summary)
    content_parts.append(
        f"\n\n来源新闻：[点击查看]({getattr(news, 'source_url', '') or f'/news/{news.id}'})")
    content = "\n\n".join(content_parts)

    post_data = PostCreate(
        title=title,
        content=content,
        category=data.category,
        cover_image=news.cover_image,
        images=None,
        attachments=None,
    )

    post = await forum_service.create_post(db, current_user.id, post_data)

    return NewsToForumPostResponse(
        post_id=int(post.id),
        post_title=post.title,
        post_url=f"/forum/post/{int(post.id)}",
        message="已成功将新闻转发到论坛讨论",
    )
