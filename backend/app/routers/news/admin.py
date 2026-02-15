"""News admin routes

Provides news management endpoints for administrators
"""
import json
from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, desc, func, and_, or_, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from ...database import get_db
from ...models.news import News, NewsComment, NewsTopicItem, NewsSource, NewsIngestRun
from ...models.news_ai import NewsAIAnnotation
from ...models.notification import Notification, NotificationType
from ...models.system import AdminLog
from ...models.user import User
from ...schemas.news import (
    NewsCreate,
    NewsUpdate,
    NewsResponse,
    NewsListResponse,
    NewsListItem,
    NewsAdminListResponse,
    NewsAdminListItem,
    NewsTopicCreate,
    NewsTopicUpdate,
    NewsTopicResponse,
    NewsTopicListResponse,
    NewsTopicDetailResponse,
    NewsTopicItemCreate,
    NewsTopicItemBrief,
    NewsTopicReportItem,
    NewsTopicReportResponse,
    NewsSourceCreate,
    NewsSourceUpdate,
    NewsSourceResponse,
    NewsSourceListResponse,
    NewsIngestRunResponse,
    NewsIngestRunListResponse,
    NewsSourceHealthItem,
    NewsSourceHealthListResponse,
    NewsReviewAction,
    NewsCommentReviewAction,
    NewsCommentAdminItem,
    NewsCommentAdminListResponse,
    NewsVersionItem,
    NewsVersionListResponse,
    NewsRollbackRequest,
    NewsAIGenerateRequest,
    NewsAIGenerationItem,
    NewsAIGenerationListResponse,
    NewsLinkCheckRequest,
    NewsLinkCheckItem,
    NewsLinkCheckResponse,
    NewsBatchActionRequest,
    NewsBatchActionResponse,
    NewsBatchQueryRequest,
    ScheduledNewsItem,
    ScheduledNewsListResponse,
    NewsAIAnnotationResponse,
)
from ...services.news_service import news_service
from ...services.news_workbench_service import news_workbench_service
from ...services.rss_ingest_service import rss_ingest_service
from ...utils.deps import require_admin
from ...utils.helpers import _coerce_int
from ...config import get_settings
from ...utils.rate_limiter import get_client_ip

router = APIRouter(prefix="/admin", tags=["News Admin"])


# ============ News Source Management ============

@router.get("/sources", response_model=NewsSourceListResponse,
            summary="Get news sources")
async def admin_list_news_sources(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get list of news RSS sources"""
    res = await db.execute(select(NewsSource).order_by(NewsSource.id.asc()))
    rows = list(res.scalars().all())
    return NewsSourceListResponse(
        items=[NewsSourceResponse.model_validate(s) for s in rows])


@router.post("/sources", response_model=NewsSourceResponse,
             summary="Create news source")
async def admin_create_news_source(
    data: NewsSourceCreate,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new RSS news source"""
    feed_url = str(getattr(data, "feed_url", "") or "").strip()
    if not feed_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="feed_url不能为空")

    src = NewsSource(
        name=str(getattr(data, "name", "") or "").strip() or feed_url,
        source_type="rss",
        feed_url=feed_url,
        site=str(getattr(data, "site", None) or "").strip() or None,
        category=str(getattr(data, "category", None)
                     or "").strip().lower() or None,
        is_enabled=bool(getattr(data, "is_enabled", True)),
        fetch_timeout_seconds=getattr(data, "fetch_timeout_seconds", None),
        max_items_per_feed=getattr(data, "max_items_per_feed", None),
    )
    db.add(src)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="feed_url已存在")
    await db.refresh(src)
    return NewsSourceResponse.model_validate(src)


@router.put("/sources/{source_id}",
            response_model=NewsSourceResponse, summary="Update news source")
async def admin_update_news_source(
    source_id: int,
    data: NewsSourceUpdate,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a news source"""
    res = await db.execute(select(NewsSource).where(NewsSource.id == int(source_id)))
    src = res.scalar_one_or_none()
    if src is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="来源不存在")

    feed_url = str(getattr(data, "feed_url", "") or "").strip()
    if feed_url:
        src.feed_url = feed_url
    site = getattr(data, "site", None)
    if site is not None:
        src.site = site.strip() if site else None
    category = getattr(data, "category", None)
    if category is not None:
        src.category = category.strip().lower()
    is_enabled = getattr(data, "is_enabled", None)
    if is_enabled is not None:
        src.is_enabled = bool(is_enabled)
    fetch_timeout = getattr(data, "fetch_timeout_seconds", None)
    if fetch_timeout is not None:
        src.fetch_timeout_seconds = int(fetch_timeout)
    max_items = getattr(data, "max_items_per_feed", None)
    if max_items is not None:
        src.max_items_per_feed = int(max_items)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="feed_url已存在")
    await db.refresh(src)
    return NewsSourceResponse.model_validate(src)


@router.delete("/sources/{source_id}", summary="Delete news source")
async def admin_delete_news_source(
    source_id: int,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a news source"""
    res = await db.execute(select(NewsSource).where(NewsSource.id == int(source_id)))
    src = res.scalar_one_or_none()
    if src is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="来源不存在")

    _ = await db.execute(delete(NewsIngestRun).where(NewsIngestRun.source_id == int(source_id)))
    await db.delete(src)
    await db.commit()
    return {"message": "删除成功"}


@router.get("/sources/health", response_model=NewsSourceHealthListResponse,
            summary="Get source health")
async def admin_list_news_sources_health(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit_per_source: Annotated[int, Query(ge=1, le=200)] = 20,
):
    """Get health status of news sources"""
    limit = max(1, min(200, int(limit_per_source)))

    src_res = await db.execute(select(NewsSource).order_by(NewsSource.id.asc()))
    sources = list(src_res.scalars().all())

    items: list[NewsSourceHealthItem] = []
    for s in sources:
        run_res = await db.execute(
            select(NewsIngestRun).where(
                NewsIngestRun.source_id == int(
                    s.id)).order_by(
                NewsIngestRun.created_at.desc()).limit(limit)
        )
        runs = list(run_res.scalars().all())

        last_run = runs[0] if runs else None
        last_success = None
        errors = []
        for r in runs:
            if r.status == "success":
                if last_success is None:
                    last_success = r
            else:
                errors.append(r.last_error or "Unknown error")

        items.append(
            NewsSourceHealthItem(
                source_id=int(s.id),
                recent_total=0,
                recent_failed=0,
                failure_rate=0.0,
                last_status=last_run.status if last_run else None,
                last_run_at=getattr(
                    last_run, "created_at", None) if last_run else None,
                last_success_at=getattr(
                    last_success,
                    "created_at",
                    None) if last_success else None,
                last_error=", ".join(errors[:3]) if errors else None,
                last_error_at=getattr(
                    last_run,
                    "created_at",
                    None) if last_run and last_run.status != "success" else None,
            )
        )

    return NewsSourceHealthListResponse(
        limit_per_source=int(limit), items=items)


@router.post("/sources/{source_id}/ingest/run-once",
             summary="Trigger source ingest")
async def admin_run_ingest_once(
    source_id: int,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Manually trigger RSS ingest for a source"""
    res = await db.execute(select(NewsSource.id).where(NewsSource.id == int(source_id)))
    exists = res.scalar_one_or_none()
    if exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="来源不存在")

    stats = await rss_ingest_service.run_once(db, source_id=int(source_id))
    return {"message": "ok", **{k: int(v) for k, v in stats.items()}}


@router.get("/ingest-runs", response_model=NewsIngestRunListResponse,
            summary="Get ingest runs")
async def admin_list_ingest_runs(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    source_id: int | None = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    from_dt: Annotated[str | None, Query(alias="from")] = None,
    to_dt: Annotated[str | None, Query(alias="to")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Get RSS ingest run history"""
    page = max(1, int(page))
    page_size = min(100, max(1, int(page_size)))

    conditions: list[ColumnElement[bool]] = []
    if source_id is not None:
        conditions.append(NewsIngestRun.source_id == int(source_id))
    if status_filter is not None and str(status_filter).strip():
        conditions.append(NewsIngestRun.status == str(status_filter).strip())

    if from_dt is not None and str(from_dt).strip():
        raw = str(from_dt).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="invalid from")
        conditions.append(NewsIngestRun.created_at >= parsed)

    if to_dt is not None and str(to_dt).strip():
        raw = str(to_dt).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="invalid to")
        conditions.append(NewsIngestRun.created_at <= parsed)

    where_clause = and_(*conditions) if conditions else None

    base = select(NewsIngestRun)
    if where_clause is not None:
        base = base.where(where_clause)

    total_q = select(func.count(NewsIngestRun.id))
    if where_clause is not None:
        total_q = total_q.where(where_clause)
    total_res = await db.execute(total_q)
    total = int(total_res.scalar() or 0)

    q = base.order_by(
        NewsIngestRun.created_at.desc()).offset(
        (page - 1) * page_size).limit(page_size)
    res = await db.execute(q)
    items = list(res.scalars().all())

    return NewsIngestRunListResponse(
        items=[
            NewsIngestRunResponse.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size)


# ============ News CRUD ============

@router.get("/topics/report", response_model=NewsTopicReportResponse,
            summary="Get topics report")
async def admin_list_topics_report(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get report of all topics with their stats"""
    topics = await news_service.list_topics(db, active_only=True)

    items: list[NewsTopicReportItem] = []
    for topic in topics:
        tid = int(getattr(topic, "id", 0) or 0)
        if tid <= 0:
            continue

        news_count_res = await db.execute(
            select(
                func.count(
                    NewsTopicItem.id)).where(
                NewsTopicItem.topic_id == tid)
        )
        news_count = int(news_count_res.scalar() or 0)

        items.append(NewsTopicReportItem(
            id=tid,
            title=str(getattr(topic, "title", "") or ""),
            is_active=bool(getattr(topic, "is_active", True)),
            news_count=news_count,
        ))

    return NewsTopicReportResponse(items=items)


# ============ News Comments Management ============

@router.get("/comments", response_model=NewsCommentAdminListResponse,
            summary="Get comments list")
async def admin_list_comments(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    keyword: str | None = None,
    include_deleted: bool = False,
):
    """Get list of news comments for admin"""
    conditions = []
    if keyword:
        conditions.append(NewsComment.content.ilike(f"%{keyword}%"))
    if not include_deleted:
        conditions.append(NewsComment.is_deleted == False)

    where_clause = and_(*conditions) if conditions else None

    base = select(NewsComment)
    if where_clause is not None:
        base = base.where(where_clause)

    total_q = select(func.count(NewsComment.id))
    if where_clause is not None:
        total_q = total_q.where(where_clause)
    total_res = await db.execute(total_q)
    total = int(total_res.scalar() or 0)

    q = base.order_by(desc(NewsComment.created_at)).offset(
        (page - 1) * page_size).limit(page_size)
    res = await db.execute(q)
    items = list(res.scalars().all())

    return NewsCommentAdminListResponse(
        items=[NewsCommentAdminItem.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/comments/{comment_id}/review",
             response_model=NewsCommentAdminItem, summary="Review comment")
async def admin_review_comment(
    comment_id: int,
    data: NewsCommentReviewAction,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Review/approve/reject a comment"""
    action = str(data.action or "").strip().lower()
    if action not in {"approve", "reject", "pending"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action 仅支持 approve / reject / pending")

    res = await db.execute(select(NewsComment).where(NewsComment.id == comment_id))
    comment = res.scalar_one_or_none()
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在")

    if action == "approve":
        comment.review_status = "approved"
    elif action == "reject":
        comment.review_status = "rejected"
    else:
        comment.review_status = "pending"
    comment.review_reason = data.reason

    await db.commit()
    await db.refresh(comment)

    return NewsCommentAdminItem.model_validate(comment)


class BatchCommentReviewAction(BaseModel):
    ids: list[int]
    action: str
    reason: str | None = None


@router.post("/comments/review/batch", summary="Batch review comments")
async def admin_batch_review_comments(
    data: BatchCommentReviewAction,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Batch approve/reject comments"""
    ids = [int(x) for x in (data.ids or []) if int(x) > 0]
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ids 不能为空")

    action = str(data.action or "").strip().lower()
    if action not in {"approve", "reject", "pending"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action 仅支持 approve / reject / pending")

    res = await db.execute(select(NewsComment).where(NewsComment.id.in_(ids)))
    comments = list(res.scalars().all())

    processed: list[int] = []
    for comment in comments:
        if action == "approve":
            comment.review_status = "approved"
        elif action == "reject":
            comment.review_status = "rejected"
        else:
            comment.review_status = "pending"
        comment.review_reason = data.reason
        processed.append(int(comment.id))

    await db.commit()

    return {
        "processed": processed,
        "action": action,
        "reason": data.reason,
    }


@router.post("", response_model=NewsResponse, summary="Create news")
async def create_news(
    data: NewsCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new news article (admin only)"""
    news = await news_service.create(db, data, admin_user_id=int(current_user.id))
    if news.is_published:
        _ = await news_service.notify_subscribers_on_publish(db, news)
    return NewsResponse.model_validate(news)


@router.put("/{news_id}", response_model=NewsResponse, summary="Update news")
async def update_news(
    news_id: int,
    data: NewsUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a news article (admin only)"""
    news = await news_service.get_by_id(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found")

    was_published = bool(news.is_published)
    updated_news = await news_service.update(db, news, data, admin_user_id=int(current_user.id))

    if (not was_published) and bool(updated_news.is_published):
        _ = await news_service.notify_subscribers_on_publish(db, updated_news)
    return NewsResponse.model_validate(updated_news)


@router.delete("/{news_id}", summary="Delete news")
async def delete_news(
    news_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a news article (admin only)"""
    _ = current_user
    news = await news_service.get_by_id(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found")

    await news_service.delete(db, news)
    return {"message": "News deleted successfully"}


# ============ News List ============

@router.get("", response_model=NewsAdminListResponse,
            summary="Get all news (including unpublished)")
async def get_all_news(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
    review_status: str | None = None,
    risk_level: str | None = None,
    source_site: str | None = None,
    source: str | None = None,
    topic_id: int | None = None,
):
    """Get all news including unpublished (admin only)"""
    _ = current_user
    news_list, total = await news_service.get_list(
        db, page, page_size, category, keyword,
        published_only=False,
        review_status=review_status,
        ai_risk_level=risk_level,
        source_site=source_site,
        source=source,
        topic_id=int(topic_id) if topic_id is not None else None,
    )

    ids = [int(n.id) for n in news_list]
    risk_levels = await _get_ai_risk_levels(db, ids)

    items: list[NewsAdminListItem] = []
    for news in news_list:
        item = NewsAdminListItem.model_validate(news)
        item.ai_risk_level = risk_levels.get(int(news.id), "unknown")
        items.append(item)
    return NewsAdminListResponse(
        items=items, total=total, page=page, page_size=page_size)


@router.get("/all", response_model=NewsAdminListResponse,
            summary="Get all news (alias for /)")
async def get_all_news_alias(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    keyword: str | None = None,
    review_status: str | None = None,
    risk_level: str | None = None,
    source_site: str | None = None,
    source: str | None = None,
    topic_id: int | None = None,
):
    """Get all news including unpublished (admin only) - alias for /"""
    return await get_all_news(current_user, db, page, page_size, category, keyword, review_status, risk_level, source_site, source, topic_id)


@router.get("/{news_id}", response_model=NewsResponse,
            summary="Get news detail (admin)")
async def admin_get_news_detail(
    news_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get news detail including unpublished (admin only, no view count increment)"""
    _ = current_user
    news = await news_service.get_by_id(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found")

    resp = NewsResponse.model_validate(news)

    ann_res = await db.execute(select(NewsAIAnnotation).where(NewsAIAnnotation.news_id == int(news.id)))
    ann = ann_res.scalar_one_or_none()
    if ann is not None:
        raw_words = str(getattr(ann, "sensitive_words", "") or "").strip()
        words = [w.strip() for w in raw_words.split(
            ",") if w.strip()] if raw_words else []

        highlights: list[str] = []
        try:
            raw_hl = getattr(ann, "highlights", None)
            parsed_hl = json.loads(raw_hl) if isinstance(
                raw_hl, str) and raw_hl.strip() else []
            if isinstance(parsed_hl, list):
                for x in parsed_hl:
                    s = str(x or "").strip()
                    if s:
                        highlights.append(s)
        except Exception:
            highlights = []

        keywords: list[str] = []
        try:
            raw_kw = getattr(ann, "keywords", None)
            parsed_kw = json.loads(raw_kw) if isinstance(
                raw_kw, str) and raw_kw.strip() else []
            if isinstance(parsed_kw, list):
                for x in parsed_kw:
                    s = str(x or "").strip()
                    if s:
                        keywords.append(s)
        except Exception:
            keywords = []
        risk = str(getattr(ann, "risk_level", "unknown") or "unknown")
        resp.ai_risk_level = risk
        resp.ai_annotation = NewsAIAnnotationResponse(
            summary=getattr(ann, "summary", None),
            risk_level=risk,
            sensitive_words=words,
            highlights=highlights,
            keywords=keywords,
            duplicate_of_news_id=getattr(ann, "duplicate_of_news_id", None),
            processed_at=getattr(ann, "processed_at", None),
        )
    else:
        resp.ai_risk_level = "unknown"
    return resp


# ============ News Review ============

@router.post("/{news_id}/review", response_model=NewsResponse,
             summary="Review news")
async def admin_review_news(
    news_id: int,
    data: NewsReviewAction,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Review/approve or reject a news article"""
    action = str(getattr(data, "action", "") or "").strip().lower()
    if action not in {"approve", "reject", "pending"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action 仅支持 approve / reject / pending")

    was_published = False
    existing = await news_service.get_by_id(db, int(news_id))
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found")
    was_published = bool(getattr(existing, "is_published", False))

    try:
        updated = await news_service.review_news_admin(
            db, int(news_id), action=action, reason=getattr(data, "reason", None),
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效操作")

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found")

    if (not was_published) and bool(getattr(updated, "is_published", False)):
        _ = await news_service.notify_subscribers_on_publish(db, updated)

    return NewsResponse.model_validate(updated)


# ============ News Version History ============

@router.get("/{news_id}/versions",
            response_model=NewsVersionListResponse,
            summary="Get version history")
async def admin_list_news_versions(
    news_id: int,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    """Get version history for a news article"""
    versions = await news_service.list_versions(db, int(news_id), limit=int(limit))
    items = [NewsVersionItem.model_validate(v) for v in versions]
    return NewsVersionListResponse(items=items)


@router.post("/{news_id}/rollback", response_model=NewsResponse,
             summary="Rollback to version")
async def admin_rollback_news(
    news_id: int,
    data: NewsRollbackRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """Rollback news to a previous version"""
    try:
        news_obj = await news_service.get_by_id(db, int(news_id))
        if news_obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News not found")

        version_obj = await news_service.get_version_by_id(db, int(data.version_id))
        if version_obj is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="版本不存在或快照无效")

        updated = await news_service.rollback_to_version(
            db, news_obj, version_obj,
            admin_user_id=int(current_user.id),
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="版本不存在或快照无效")

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found")

    await _log_news_admin_action(
        db,
        user_id=int(current_user.id),
        action="rollback",
        module="news",
        target_id=int(news_id),
        description=f"rollback to version {int(data.version_id)}",
        request=request,
    )

    return NewsResponse.model_validate(updated)


# ============ AI Workbench ============

@router.post("/ai/generate", response_model=NewsAIGenerationItem,
             summary="AI generate content")
async def admin_news_ai_generate(
    data: NewsAIGenerateRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """Generate AI content for news workbench"""
    nid = _coerce_int(data.news_id)

    title = getattr(data, "title", None)
    summary = getattr(data, "summary", None)
    content = getattr(data, "content", None)

    use_news_content = bool(data.use_news_content)
    if use_news_content and nid is not None and nid > 0:
        t0, s0, c0 = await news_workbench_service.get_news_content_for_task(db, int(nid))
        if title is None:
            title = t0
        if summary is None:
            summary = s0
        if content is None:
            content = c0

    if not str(content or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="content 不能为空")

    task_type = str(getattr(data, "task_type", "") or "").strip()
    if not task_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task_type 不能为空")

    wc_min = _coerce_int(data.word_count_min)
    wc_max = _coerce_int(data.word_count_max)
    if wc_min is not None and wc_max is not None and int(wc_min) > int(wc_max):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="word_count_min 不能大于 word_count_max")

    rec = await news_workbench_service.generate(
        db,
        user_id=int(current_user.id),
        news_id=nid,
        task_type=task_type,
        title=title,
        summary=summary,
        content=content,
        style=getattr(data, "style", None),
        word_count_min=getattr(data, "word_count_min", None),
        word_count_max=getattr(data, "word_count_max", None),
        append=bool(getattr(data, "append", False)),
    )

    await _log_news_admin_action(
        db,
        int(current_user.id),
        "ai_generate",
        "news",
        target_id=int(nid) if nid is not None else None,
        description=f"task_type={task_type} status={str(getattr(rec, 'status', '') or '')}",
        request=request,
    )
    return NewsAIGenerationItem.model_validate(rec)


@router.get("/ai/generations", response_model=NewsAIGenerationListResponse,
            summary="List AI generations")
async def admin_list_news_ai_generations(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    news_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    """List AI generation history"""
    nid = int(news_id) if news_id is not None else None
    items = await news_workbench_service.list_generations(db, user_id=int(current_user.id), news_id=nid, limit=int(limit))

    await _log_news_admin_action(
        db,
        int(current_user.id),
        "ai_generations_list",
        "news",
        target_id=int(nid) if nid is not None else None,
        description=f"news_id={nid if nid is not None else ''} limit={int(limit)} items={len(items)}",
        request=request,
    )
    return NewsAIGenerationListResponse(
        items=[NewsAIGenerationItem.model_validate(x) for x in items])


@router.post("/{news_id}/ai/rerun", summary="Rerun AI annotation for news")
async def admin_rerun_news_ai(
    news_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """Rerun AI pipeline for a specific news article"""
    from ...services.news_ai_pipeline_service import news_ai_pipeline_service

    news = await news_service.get_by_id(db, news_id)
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在")

    await news_ai_pipeline_service.rerun_news(db, news_id)

    await _log_news_admin_action(
        db,
        int(current_user.id),
        "ai_rerun",
        "news",
        target_id=int(news_id),
        description=f"news_id={news_id}",
        request=request,
    )
    return {"message": "ok"}


# ============ Link Check ============

@router.post("/link_check", response_model=NewsLinkCheckResponse,
             summary="Check links in content")
async def admin_check_news_links(
    data: NewsLinkCheckRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """Extract and check links in markdown content"""
    nid = _coerce_int(data.news_id)
    markdown = data.markdown

    use_news_content = bool(data.use_news_content)
    if (markdown is None) and use_news_content and nid is not None and nid > 0:
        _, _, c0 = await news_workbench_service.get_news_content_for_task(db, int(nid))
        markdown = c0
    md = str(markdown or "")

    if not md.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="markdown 不能为空")

    run_id, items = await news_workbench_service.check_links(
        db,
        user_id=int(current_user.id),
        news_id=nid,
        markdown=md,
        timeout_seconds=float(data.timeout_seconds or 6.0),
        max_urls=int(data.max_urls or 50),
    )

    await _log_news_admin_action(
        db,
        int(current_user.id),
        "link_check",
        "news",
        target_id=int(nid) if nid is not None else None,
        description=f"run_id={str(run_id)} urls={len(items)}",
        request=request,
    )

    return NewsLinkCheckResponse(
        run_id=str(run_id),
        items=[NewsLinkCheckItem.model_validate(x) for x in items],
    )


@router.get("/link_check/{run_id}", response_model=NewsLinkCheckResponse,
            summary="Get link check result")
async def admin_get_link_check_result(
    run_id: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """Get link check result by run_id"""
    rid = str(run_id or "").strip()
    if not rid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="run_id 不能为空")

    items = await news_workbench_service.get_link_checks_by_run_id(db, run_id=rid, user_id=int(current_user.id))

    await _log_news_admin_action(
        db,
        int(current_user.id),
        "link_check_get",
        "news",
        target_id=None,
        description=f"run_id={rid} items={len(items)}",
        request=request,
    )

    return NewsLinkCheckResponse(
        run_id=rid, items=[NewsLinkCheckItem.model_validate(x) for x in items])


# ============ Batch Operations ============

class BatchReviewAction(BaseModel):
    ids: list[int]
    action: str
    reason: str | None = None


@router.post("/batch", response_model=NewsBatchActionResponse,
             summary="Batch action on news")
async def admin_batch_action_news(
    data: NewsBatchActionRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """Perform batch action on multiple news items"""
    raw_ids = [int(x) for x in (data.ids or []) if int(x) > 0]
    seen: set[int] = set()
    ids: list[int] = []
    for i in raw_ids:
        if int(i) not in seen:
            ids.append(int(i))
            seen.add(int(i))
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ids 不能为空")

    action = str(getattr(data, "action", "") or "").strip().lower()
    reason = str(getattr(data, "reason", "") or "").strip() or None

    allowed = {"publish", "unpublish", "top", "untop", "rerun_ai"}
    if action not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action 不支持")

    res = await db.execute(select(News).where(News.id.in_(ids)))
    items = list(res.scalars().all())
    found_ids = {int(n.id) for n in items}
    missing_ids = [int(i) for i in ids if int(i) not in found_ids]

    processed: list[int] = []
    skipped: list[int] = []

    if action == "rerun_ai":
        from ...services.news_ai_pipeline_service import news_ai_pipeline_service

        for n in items:
            try:
                await news_ai_pipeline_service.rerun_news(db, int(n.id))
                processed.append(int(n.id))
            except Exception:
                skipped.append(int(n.id))

        msg = f"已处理 {len(processed)} 条，跳过 {len(skipped)} 条，缺失 {len(missing_ids)} 条"
        await _log_news_admin_action(
            db,
            int(current_user.id),
            "batch_rerun_ai",
            "news",
            target_id=None,
            description=msg,
            request=request,
        )
        return NewsBatchActionResponse(
            requested=ids,
            processed=processed,
            missing=missing_ids,
            skipped=skipped,
            action=action,
            reason=reason,
            message=msg,
        )

    updated_items: list[News] = []
    for n in items:
        if action == "publish":
            if str(getattr(n, "review_status", "approved")
                   or "approved").strip().lower() != "approved":
                skipped.append(int(n.id))
                continue
            upd = NewsUpdate(is_published=True)
        elif action == "unpublish":
            upd = NewsUpdate(is_published=False)
        elif action == "top":
            upd = NewsUpdate(is_top=True)
        else:
            upd = NewsUpdate(is_top=False)

        try:
            updated = await news_service.update(
                db,
                n,
                upd,
                admin_user_id=int(current_user.id),
                change_desc=reason,
            )
            updated_items.append(updated)
            processed.append(int(n.id))
        except Exception:
            skipped.append(int(n.id))

    published_new: list[News] = []
    if action == "publish":
        for n in updated_items:
            if int(n.id) in processed and bool(
                    getattr(n, "is_published", False)):
                published_new.append(n)

    notifications_created = 0
    for n in published_new:
        try:
            notifications_created += int(await news_service.notify_subscribers_on_publish(db, n))
        except Exception:
            continue

    msg = f"已处理 {len(processed)} 条，跳过 {len(skipped)} 条，缺失 {len(missing_ids)} 条"
    if notifications_created:
        msg += f"，推送 {int(notifications_created)} 条"

    await _log_news_admin_action(
        db,
        int(current_user.id),
        f"batch_{action}",
        "news",
        target_id=None,
        description=msg,
        request=request,
    )

    return NewsBatchActionResponse(
        requested=ids,
        processed=processed,
        missing=missing_ids,
        skipped=skipped,
        action=action,
        reason=reason,
        message=msg,
    )


@router.post("/batch/query", response_model=NewsBatchActionResponse,
             summary="Batch action by query")
async def admin_batch_action_news_by_query(
    data: NewsBatchQueryRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """Perform batch action on news matching query criteria"""
    action = str(data.action or "").strip().lower()
    if action != "rerun_ai":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action 仅支持 rerun_ai")

    limit = int(data.limit or 200)
    limit = max(1, min(500, limit))

    topic_id = _coerce_int(data.topic_id)

    news_list, total = await news_service.get_list(
        db,
        page=1,
        page_size=limit,
        category=data.category,
        keyword=data.keyword,
        published_only=False,
        review_status=data.review_status,
        ai_risk_level=data.risk_level,
        source_site=data.source_site,
        source=data.source,
        topic_id=int(topic_id) if topic_id is not None else None,
    )

    ids = [int(n.id) for n in news_list]
    processed: list[int] = []
    skipped: list[int] = []

    from ...services.news_ai_pipeline_service import news_ai_pipeline_service

    for nid in ids:
        try:
            await news_ai_pipeline_service.rerun_news(db, int(nid))
            processed.append(int(nid))
        except Exception:
            skipped.append(int(nid))

    msg = (
        f"已处理 {len(processed)} 条，跳过 {len(skipped)} 条，"
        f"本次命中 {len(ids)} 条，筛选总数 {int(total)} 条"
    )
    await _log_news_admin_action(
        db,
        int(current_user.id),
        "batch_query_rerun_ai",
        "news",
        target_id=None,
        description=msg,
        request=request,
    )

    return NewsBatchActionResponse(
        requested=ids,
        processed=processed,
        missing=[],
        skipped=skipped,
        action=action,
        reason=None,
        message=msg,
    )


# ============ Scheduled News ============

@router.get("/scheduled", response_model=ScheduledNewsListResponse,
            summary="List scheduled news")
async def admin_list_scheduled_news(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
):
    """List news scheduled for publish/unpublish"""
    q = (select(News) .where(or_(News.scheduled_publish_at.is_not(None),
                                 News.scheduled_unpublish_at.is_not(None),
                                 )) .order_by(desc(News.scheduled_publish_at),
                                              desc(News.scheduled_unpublish_at),
                                              desc(News.id)) .limit(int(limit)))
    res = await db.execute(q)
    items = list(res.scalars().all())

    await _log_news_admin_action(
        db,
        int(current_user.id),
        "scheduled_list",
        "news",
        target_id=None,
        description=f"limit={int(limit)} items={len(items)}",
        request=request,
    )
    return ScheduledNewsListResponse(
        items=[ScheduledNewsItem.model_validate(x) for x in items])


# ============ Batch Review ============

@router.post("/review/batch", summary="Batch review news")
async def admin_batch_review_news(
    data: BatchReviewAction,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """Batch approve/reject/pending news"""
    ids = [int(x) for x in (data.ids or []) if int(x) > 0]
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ids 不能为空")

    action = (data.action or "").strip().lower()
    if action not in {"approve", "reject", "pending"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="action 仅支持 approve / reject / pending",
        )

    result = await db.execute(select(News).where(News.id.in_(ids)))
    items = list(result.scalars().all())
    found_ids = {int(n.id) for n in items}
    missing_ids = [int(i) for i in ids if int(i) not in found_ids]

    now = datetime.now()
    rsn = str(data.reason).strip() if data.reason is not None else None

    became_published: list[News] = []
    processed: list[int] = []

    for news in items:
        prev_published = bool(getattr(news, "is_published", False))
        if action == "approve":
            news.review_status = "approved"
            news.review_reason = rsn
            news.reviewed_at = now

            sp = getattr(news, "scheduled_publish_at", None)
            su = getattr(news, "scheduled_unpublish_at", None)
            if isinstance(sp, datetime) and sp <= now and (
                su is None or (isinstance(su, datetime) and su > now)
            ):
                news.is_published = True
                news.published_at = now
        elif action == "reject":
            news.review_status = "rejected"
            news.review_reason = rsn
            news.reviewed_at = now
            news.is_published = False
            news.published_at = None
        else:
            news.review_status = "pending"
            news.review_reason = rsn
            news.reviewed_at = None
            news.is_published = False
            news.published_at = None

        if (not prev_published) and bool(getattr(news, "is_published", False)):
            became_published.append(news)

        processed.append(int(news.id))

    await db.commit()

    notifications_created = 0
    for news in became_published:
        notifications_created += int(await news_service.notify_subscribers_on_publish(db, news))

    counts = {
        "requested": len(ids),
        "processed": len(processed),
        "missing": len(missing_ids),
        "notifications_created": int(notifications_created),
    }
    message = f"已处理 {counts['processed']} 条，缺失 {counts['missing']} 条"

    await _log_news_admin_action(
        db,
        int(current_user.id),
        f"review_batch_{action}",
        "news",
        target_id=None,
        description=message,
        request=request,
    )
    return {
        "processed": processed,
        "missing": missing_ids,
        "action": action,
        "reason": rsn,
        "requested": ids,
        "counts": counts,
        "message": message,
    }


# ============ DEBUG Endpoints ============

class AdminDebugSetViewCountRequest(BaseModel):
    view_count: int


@router.post("/{news_id}/debug/set-view-count",
             summary="DEBUG: Set view count")
async def admin_debug_set_view_count(
    news_id: int,
    data: AdminDebugSetViewCountRequest,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """DEBUG: Set news view count (only in debug mode)"""
    settings = get_settings()
    if not bool(getattr(settings, "debug", False)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="not found")

    vc = int(getattr(data, "view_count", 0) or 0)
    if vc < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="view_count must be >= 0")

    result = await db.execute(
        update(News).where(News.id == int(news_id)).values(view_count=int(vc))
    )
    await db.commit()
    if not int(getattr(result, "rowcount", 0) or 0):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="新闻不存在")

    await news_service.invalidate_hot_cache()
    return {"message": "ok", "news_id": int(news_id), "view_count": int(vc)}


# ============ Helper Functions ============

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


async def _log_news_admin_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    module: str,
    target_id: int | None = None,
    description: str | None = None,
    request: Request | None = None,
) -> None:
    """Log admin action for news module"""
    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = get_client_ip(request)
        user_agent = request.headers.get(
            "user-agent", "")[:500] if request.headers else None

    log = AdminLog(
        user_id=int(user_id),
        action=str(action),
        module=str(module),
        target_id=int(target_id) if target_id is not None else None,
        target_type=None,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_data=None,
    )
    db.add(log)
    await db.flush()
