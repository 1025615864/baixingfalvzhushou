from __future__ import annotations

import time
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession


class NewsService:
    def __init__(self):
        self._articles: dict[int, dict] = {}
        self._next_id = 1
        self._cache: dict[str, tuple] = {}

    async def create(self, db: AsyncSession, news_data=None, admin_user_id: int = None, **kwargs) -> object:
        from app.models.news import News
        data = {}
        if news_data:
            for field in ("title", "content", "category", "source", "source_url", "cover_image", "author", "is_published", "is_top", "summary", "source_site"):
                val = getattr(news_data, field, None)
                if val is not None:
                    data[field] = val
        data.setdefault("is_published", False)
        news = News(**data)
        db.add(news)
        await db.flush()
        await db.refresh(news)
        return news

    async def get_by_id(self, db: AsyncSession, news_id: int) -> Optional[object]:
        from app.models.news import News
        stmt = select(News).where(News.id == news_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(self, db: AsyncSession, page: int = 1, page_size: int = 10, category: str | None = None, keyword: str | None = None) -> tuple[list, int]:
        from app.models.news import News
        conditions = [News.is_published.is_(True)]
        if category:
            conditions.append(News.category == category)
        if keyword:
            conditions.append(News.title.ilike(f"%{keyword}%"))
        count_stmt = select(func.count()).select_from(News).where(*conditions)
        result = await db.execute(count_stmt)
        total = result.scalar() or 0
        stmt = select(News).where(*conditions).order_by(News.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(stmt)
        news_list = result.scalars().all()
        return news_list, total

    async def update(self, db: AsyncSession, news, news_data=None, admin_user_id: int = None, **kwargs) -> object:
        if news_data:
            for field, value in news_data:
                if value is not None:
                    setattr(news, field, value)
        await db.flush()
        await db.refresh(news)
        return news

    async def delete(self, db: AsyncSession, news) -> None:
        await db.delete(news)
        await db.commit()

    async def increment_view(self, db: AsyncSession, news_id: int) -> None:
        from app.models.news import News
        stmt = sa_update(News).where(News.id == news_id).values(view_count=News.view_count + 1)
        await db.execute(stmt)
        await db.commit()

    async def get_hot_news(self, db: AsyncSession, limit: int = 10, days: int | None = None) -> list:
        from app.models.news import News
        conditions = [News.is_published.is_(True)]
        if days is not None and days > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            conditions.append(News.created_at >= cutoff)
        stmt = select(News).where(*conditions).order_by(News.view_count.desc()).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_published(self, db: AsyncSession, news_id: int | None = None, page: int = 1, page_size: int = 10, category: str | None = None, keyword: str | None = None) -> object | tuple[list, int]:
        if news_id is not None:
            from app.models.news import News
            stmt = select(News).where(News.id == news_id, News.is_published.is_(True))
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        return await self.get_list(db, page=page, page_size=page_size, category=category, keyword=keyword)

    def _prune_cache(self, cache: dict, ttl_seconds: int = 300, now_ts: float = None, max_size: int = 100) -> None:
        if now_ts is None:
            now_ts = time.time()
        expired_keys = [k for k, (ts, _) in cache.items() if now_ts - ts > ttl_seconds]
        for k in expired_keys:
            del cache[k]
        if len(cache) > max_size:
            sorted_keys = sorted(cache.keys(), key=lambda k: cache[k][0])
            for k in sorted_keys[:len(cache) - max_size]:
                del cache[k]

    def _snapshot_json(self, news) -> str:
        return json.dumps(self._news_snapshot(news), ensure_ascii=False, default=str)

    def _escape_like(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def _news_snapshot(self, news) -> dict:
        return {
            "id": getattr(news, "id", None),
            "title": getattr(news, "title", None),
            "summary": getattr(news, "summary", None),
            "content": getattr(news, "content", None),
            "cover_image": getattr(news, "cover_image", None),
            "category": getattr(news, "category", None),
            "source": getattr(news, "source", None),
            "source_url": getattr(news, "source_url", None),
            "source_site": getattr(news, "source_site", None),
            "author": getattr(news, "author", None),
            "is_top": getattr(news, "is_top", None),
            "is_published": getattr(news, "is_published", None),
            "review_status": getattr(news, "review_status", None),
            "review_reason": getattr(news, "review_reason", None),
            "reviewed_at": str(getattr(news, "reviewed_at", "")) if getattr(news, "reviewed_at", None) else None,
            "published_at": str(getattr(news, "published_at", "")) if getattr(news, "published_at", None) else None,
            "scheduled_publish_at": str(getattr(news, "scheduled_publish_at", "")) if getattr(news, "scheduled_publish_at", None) else None,
            "scheduled_unpublish_at": str(getattr(news, "scheduled_unpublish_at", "")) if getattr(news, "scheduled_unpublish_at", None) else None,
            "created_at": str(getattr(news, "created_at", "")) if getattr(news, "created_at", None) else None,
            "updated_at": str(getattr(news, "updated_at", "")) if getattr(news, "updated_at", None) else None,
        }


news_service = NewsService()
