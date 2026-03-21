"""新闻服务核心

提供新闻 CRUD、统计、缓存等核心功能
"""
import json
import logging
from collections.abc import Mapping, MutableMapping, Sequence
from datetime import datetime
from typing import Any, cast

from sqlalchemy import select, func, and_, or_, desc, delete, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.news import (
    News,
    NewsFavorite,
    NewsViewHistory,
    NewsSubscription,
    NewsTopic,
    NewsTopicItem,
    NewsComment,
)
from ...models.news_workbench import NewsVersion
from ...schemas.news import NewsCreate, NewsUpdate
from .topics import news_topic_service
from .comments import news_comment_service
from .subscriptions import news_subscription_service
from ...utils.query_optimizer import apply_news_preload, track_query, get_query_optimizer


logger = logging.getLogger(__name__)


class NewsService:
    """新闻服务"""

    @staticmethod
    def _escape_like(value: str, escape: str = "\\") -> str:
        s = str(value or "")
        if not escape:
            return s
        s = s.replace(escape, escape + escape)
        s = s.replace("%", escape + "%")
        s = s.replace("_", escape + "_")
        return s

    @staticmethod
    def _news_snapshot(news: News) -> dict[str, object]:
        def _dt(v: object) -> str | None:
            if isinstance(v, datetime):
                return v.isoformat()
            return None

        return {
            "id": int(getattr(news, "id", 0) or 0),
            "title": str(getattr(news, "title", "") or ""),
            "summary": getattr(news, "summary", None),
            "content": str(getattr(news, "content", "") or ""),
            "cover_image": getattr(news, "cover_image", None),
            "category": str(getattr(news, "category", "") or ""),
            "source": getattr(news, "source", None),
            "source_url": getattr(news, "source_url", None),
            "source_site": getattr(news, "source_site", None),
            "author": getattr(news, "author", None),
            "is_top": bool(getattr(news, "is_top", False)),
            "is_published": bool(getattr(news, "is_published", False)),
            "review_status": str(getattr(news, "review_status", "") or ""),
            "review_reason": getattr(news, "review_reason", None),
            "reviewed_at": _dt(getattr(news, "reviewed_at", None)),
            "published_at": _dt(getattr(news, "published_at", None)),
            "scheduled_publish_at": _dt(getattr(news, "scheduled_publish_at", None)),
            "scheduled_unpublish_at": _dt(getattr(news, "scheduled_unpublish_at", None)),
            "created_at": _dt(getattr(news, "created_at", None)),
            "updated_at": _dt(getattr(news, "updated_at", None)),
        }

    @staticmethod
    def _snapshot_json(news: News) -> str:
        return json.dumps(NewsService._news_snapshot(news), ensure_ascii=False)

    # 使用 TTLCache 替代普通字典，限制缓存大小防止内存泄漏
    from cachetools import TTLCache
    
    _hot_cache: TTLCache[tuple[int, str | None, str | None], tuple[float, list[int]]] = TTLCache(
        maxsize=1000, ttl=60
    )
    _hot_cache_ttl_seconds: int = 60

    _topic_auto_cache: TTLCache[tuple[int, bool], tuple[float, list[int]]] = TTLCache(
        maxsize=500, ttl=120
    )
    _topic_auto_cache_ttl_seconds: int = 120

    _recommended_cache: TTLCache[tuple[int | None, str | None, str | None], tuple[float, list[int]]] = TTLCache(
        maxsize=1000, ttl=60
    )
    _recommended_cache_ttl_seconds: int = 60

    @staticmethod
    def _prune_cache(
        cache: MutableMapping[Any, tuple[float, list[int]]],
        ttl_seconds: int,
        now_ts: float,
        max_size: int = 2048,
    ) -> None:
        if len(cache) <= int(max_size):
            return

        expire_threshold = now_ts - ttl_seconds
        keys_to_delete = [
            k for k, (ts, _) in cache.items() if ts < expire_threshold]
        for k in keys_to_delete:
            del cache[k]

        if len(cache) <= int(max_size):
            return

        sorted_keys = sorted(
            cache.keys(),
            key=lambda k: cache[k][0])[
            :int(max_size) // 4]
        for k in sorted_keys:
            del cache[k]

    async def _compute_topic_auto_ids(
        self, db: AsyncSession, topic_id: int, only_published: bool
    ) -> list[int]:
        topic = await db.get(NewsTopic, topic_id)
        if not topic:
            return []

        auto_keyword = str(getattr(topic, "auto_keyword", "") or "").strip()
        auto_category = str(getattr(topic, "auto_category", "") or "").strip()
        auto_limit = int(getattr(topic, "auto_limit", 0) or 0)
        if auto_limit <= 0 or (not auto_keyword and not auto_category):
            return []

        base_query = select(News.id).where(News.review_status == "approved")
        if only_published:
            base_query = base_query.where(News.is_published.is_(True))
        else:
            base_query = base_query.where(News.is_published)

        if auto_category:
            base_query = base_query.where(News.category == auto_category)

        if auto_keyword:
            pattern = f"%{self._escape_like(auto_keyword)}%"
            base_query = base_query.where(
                or_(
                    News.title.ilike(pattern),
                    News.summary.ilike(pattern),
                    News.content.ilike(pattern),
                )
            )

        limit = min(int(auto_limit), 200)
        base_query = base_query.order_by(
            desc(
                News.published_at), desc(
                News.created_at)).limit(limit)
        result = await db.execute(base_query)
        return list(result.scalars().all())

    async def get_topic_auto_ids_cached(
        self, db: AsyncSession, topic_id: int, only_published: bool = True
    ) -> list[int]:
        now_ts = datetime.now().timestamp()
        self._prune_cache(
            self._topic_auto_cache,
            self._topic_auto_cache_ttl_seconds,
            now_ts)
        cache_key = (topic_id, only_published)
        cached_ts, cached_ids = self._topic_auto_cache.get(cache_key, (0, []))

        if now_ts - cached_ts < self._topic_auto_cache_ttl_seconds:
            return cached_ids

        auto_ids = await self._compute_topic_auto_ids(db, topic_id, only_published)
        self._topic_auto_cache[cache_key] = (now_ts, auto_ids)
        return auto_ids

    async def refresh_topic_auto_cache(
            self,
            db: AsyncSession,
            topic_id: int,
            published_only: bool | None = None) -> int:
        if published_only is None:
            cached = await self.get_topic_auto_ids_cached(db, topic_id, True)
            await self.get_topic_auto_ids_cached(db, topic_id, False)
            return len(cached)

        cached = await self.get_topic_auto_ids_cached(db, topic_id, bool(published_only))
        return len(cached)

    async def list_topics(self, db: AsyncSession,
                          active_only: bool = True) -> list[NewsTopic]:
        return await news_topic_service.list_topics(db, active_only=active_only)

    async def get_topic(self, db: AsyncSession,
                        topic_id: int) -> NewsTopic | None:
        return await news_topic_service.get_topic(db, topic_id)

    async def create_topic(
        self,
        db: AsyncSession,
        data: Mapping[str, Any] | Any,
        user_id: int | None = None,
    ) -> NewsTopic:
        payload: Mapping[str, Any]  # pyright: ignore
        if isinstance(data, Mapping):
            payload = data  # pyright: ignore
        elif hasattr(data, "model_dump"):
            payload = data.model_dump()  # pyright: ignore
        elif hasattr(data, "dict"):
            payload = data.dict()  # pyright: ignore
        else:
            payload = {}  # pyright: ignore
        _ = user_id
        return await news_topic_service.create_topic(db, payload)

    async def update_topic(
        self,
        db: AsyncSession,
        topic: NewsTopic | int,
        data: Mapping[str, Any] | Any,
    ) -> NewsTopic | None:
        payload: Mapping[str, Any]  # pyright: ignore
        if isinstance(data, Mapping):
            payload = data  # pyright: ignore
        elif hasattr(data, "model_dump"):
            payload = data.model_dump(exclude_unset=True)  # pyright: ignore
        elif hasattr(data, "dict"):
            payload = data.dict(exclude_unset=True)  # pyright: ignore
        else:
            payload = {}  # pyright: ignore

        topic_obj = topic
        if isinstance(topic, int):
            topic_obj = await self.get_topic(db, topic)
            if not topic_obj:
                return None
        return await news_topic_service.update_topic(db, cast(NewsTopic, topic_obj), payload)

    async def delete_topic(self, db: AsyncSession, topic_id: int) -> bool:
        topic = await self.get_topic(db, topic_id)
        if not topic:
            return False
        await news_topic_service.delete_topic(db, topic_id)
        return True

    async def list_topic_items_brief(
        self, db: AsyncSession, topic_id: int
    ) -> list[tuple[int, int, int, str | None, str | None]]:
        query = (
            select(
                NewsTopicItem.id,
                NewsTopicItem.news_id,
                NewsTopicItem.position,
                News.title,
                News.category,
            )
            .join(News, News.id == NewsTopicItem.news_id)
            .where(NewsTopicItem.topic_id == topic_id)
            .order_by(NewsTopicItem.position, NewsTopicItem.created_at)
        )
        result = await db.execute(query)
        rows = result.all()
        return [
            (
                int(row[0]),
                int(row[1]),
                int(row[2]),
                cast(str | None, row[3]),
                cast(str | None, row[4]),
            )
            for row in rows
        ]

    async def add_topic_item(
            self,
            db: AsyncSession,
            topic_id: int,
            news_id: int,
            position: int | None = None) -> NewsTopicItem:
        return await news_topic_service.add_topic_item(db, topic_id, news_id, position)

    async def add_topic_items_bulk(
        self,
        db: AsyncSession,
        topic_id: int,
        news_ids: Sequence[int],
        position_start: int | None = None,
    ) -> tuple[int, int, int]:
        requested = len(news_ids)
        if not news_ids:
            return 0, 0, 0

        existing_res = await db.execute(
            select(NewsTopicItem.news_id).where(
                NewsTopicItem.topic_id == topic_id, NewsTopicItem.news_id.in_(
                    news_ids)
            )
        )
        existing_ids = {int(x) for x in existing_res.scalars().all()}
        to_add = [int(nid) for nid in news_ids if int(nid) not in existing_ids]
        skipped = requested - len(to_add)
        if not to_add:
            return requested, 0, skipped

        if position_start is None:
            max_pos = await db.execute(
                select(func.max(NewsTopicItem.position)).where(
                    NewsTopicItem.topic_id == topic_id)
            )
            position_start = int(max_pos.scalar() or 0) + 1
        position_start = max(int(position_start or 1), 1)

        for idx, news_id in enumerate(to_add):
            item = NewsTopicItem(
                topic_id=topic_id,
                news_id=int(news_id),
                position=position_start + idx)
            db.add(item)
        await db.commit()
        return requested, len(to_add), skipped

    async def update_topic_item_position(
        self, db: AsyncSession, topic_id: int, item_id: int, position: int
    ) -> bool:
        return await news_topic_service.update_topic_item_position(db, topic_id, item_id, position)

    async def remove_topic_item(
            self, db: AsyncSession, topic_id: int, item_id: int) -> bool:
        return await news_topic_service.remove_topic_item(db, topic_id, item_id)

    async def remove_topic_items_bulk(
        self, db: AsyncSession, topic_id: int, item_ids: Sequence[int]
    ) -> tuple[int, int, int]:
        requested = len(item_ids)
        if not item_ids:
            return 0, 0, 0
        result = await db.execute(
            delete(NewsTopicItem).where(
                NewsTopicItem.topic_id == topic_id, NewsTopicItem.id.in_(
                    item_ids)
            )
        )
        await db.commit()
        deleted = int(getattr(result, "rowcount", 0) or 0)
        skipped = max(requested - deleted, 0)
        return requested, deleted, skipped

    async def reindex_topic_items(
            self, db: AsyncSession, topic_id: int) -> int:
        return await news_topic_service.reindex_topic_items(db, topic_id)

    async def reorder_topic_items(
        self, db: AsyncSession, topic_id: int, item_ids: Sequence[int]
    ) -> int:
        return await news_topic_service.reorder_topic_items(db, topic_id, item_ids)

    async def get_topic_news(
        self,
        db: AsyncSession,
        topic_id: int,
        page: int = 1,
        page_size: int = 20,
        published_only: bool = True,
    ) -> tuple[list[News], int]:
        manual_query = (
            select(
                News.id) .join(
                NewsTopicItem,
                NewsTopicItem.news_id == News.id) .where(
                NewsTopicItem.topic_id == topic_id,
                News.review_status == "approved") .order_by(
                    NewsTopicItem.position,
                NewsTopicItem.created_at))
        if published_only:
            manual_query = manual_query.where(News.is_published.is_(True))
        else:
            manual_query = manual_query.where(News.is_published)

        manual_res = await db.execute(manual_query)
        manual_ids = [int(nid) for nid in manual_res.scalars().all()]

        auto_ids = await self.get_topic_auto_ids_cached(db, topic_id, published_only)
        manual_set = set(manual_ids)
        auto_ids = [int(nid) for nid in auto_ids if int(nid) not in manual_set]

        combined_ids = manual_ids + auto_ids
        total = len(combined_ids)
        if total == 0:
            return [], 0

        start = max((int(page) - 1), 0) * int(page_size)
        end = start + int(page_size)
        page_ids = combined_ids[start:end]
        if not page_ids:
            return [], total

        order_case = case(
            {nid: idx for idx, nid in enumerate(page_ids)}, value=News.id)
        news_query = select(News).where(
            News.id.in_(page_ids)).order_by(order_case)
        news_res = await db.execute(news_query)
        return list(news_res.scalars().all()), total

    async def get_topics_report(
        self, db: AsyncSession
    ) -> list[tuple[int, str, bool, int, int, int, int]]:
        items_subq = (
            select(
                NewsTopicItem.topic_id.label("topic_id"),
                func.count(NewsTopicItem.id).label("item_count"),
                func.coalesce(func.sum(News.view_count), 0).label("view_sum"),
            )
            .join(News, News.id == NewsTopicItem.news_id)
            .group_by(NewsTopicItem.topic_id)
            .subquery()
        )
        fav_subq = (
            select(
                NewsTopicItem.topic_id.label("topic_id"),
                func.count(NewsFavorite.id).label("fav_sum"),
            )
            .join(NewsFavorite, NewsFavorite.news_id == NewsTopicItem.news_id)
            .group_by(NewsTopicItem.topic_id)
            .subquery()
        )

        query = (
            select(
                NewsTopic.id,
                NewsTopic.title,
                NewsTopic.is_active,
                NewsTopic.sort_order,
                func.coalesce(items_subq.c.item_count, 0),
                func.coalesce(items_subq.c.view_sum, 0),
                func.coalesce(fav_subq.c.fav_sum, 0),
            )
            .outerjoin(items_subq, items_subq.c.topic_id == NewsTopic.id)
            .outerjoin(fav_subq, fav_subq.c.topic_id == NewsTopic.id)
            .order_by(NewsTopic.sort_order, NewsTopic.created_at)
        )
        result = await db.execute(query)
        rows = result.all()
        return [
            (
                int(row[0]),
                str(row[1] or ""),
                bool(row[2]),
                int(row[3] or 0),
                int(row[4] or 0),
                int(row[5] or 0),
                int(row[6] or 0),
            )
            for row in rows
        ]

    async def create(
            self,
            db: AsyncSession,
            news_data: NewsCreate,
            *,
            admin_user_id: int | None = None) -> News:
        """创建新闻"""
        scheduled_publish_at = None
        is_published = news_data.is_published

        if is_published and news_data.scheduled_publish_at:
            scheduled_publish_at = news_data.scheduled_publish_at
            is_published = False
        elif is_published:
            scheduled_publish_at = datetime.now()

        news = News(
            title=news_data.title,
            summary=news_data.summary,
            content=news_data.content,
            cover_image=news_data.cover_image,
            category=news_data.category,
            source=news_data.source,
            source_url=news_data.source_url,
            source_site=news_data.source_site,
            author=news_data.author,
            is_top=news_data.is_top or False,
            is_published=is_published,
            published_at=scheduled_publish_at,
            scheduled_publish_at=news_data.scheduled_publish_at,
            scheduled_unpublish_at=news_data.scheduled_unpublish_at,
            review_status="approved" if admin_user_id else "pending",
            reviewed_at=datetime.now() if admin_user_id else None,
            reviewed_by=admin_user_id,
            created_by=admin_user_id,
        )

        db.add(news)
        await db.flush()

        version = NewsVersion(
            news_id=news.id,
            version=1,
            snapshot=self._snapshot_json(news),
            created_by=admin_user_id,
        )
        db.add(version)
        await db.commit()
        await db.refresh(news)
        return news

    async def get_by_id(self, db: AsyncSession, news_id: int) -> News | None:
        """根据ID获取新闻"""
        result = await db.execute(select(News).where(News.id == news_id))
        return result.scalar_one_or_none()

    async def get_published(self, db: AsyncSession,
                            news_id: int) -> News | None:
        """获取已发布的新闻 - 使用预加载优化"""
        query = select(News).where(
            News.id == news_id,
            News.is_published,
            or_(News.review_status == "approved",
                News.review_status is None),
        )
        # 应用预加载优化 - 使用 selectinload 预加载 AI 标注信息
        query = apply_news_preload(query, level="basic")
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        keyword: str | None = None,
        published_only: bool = True,
        review_status: str | None = None,
        ai_risk_level: str | None = None,
        source_site: str | None = None,
        source: str | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        is_top: bool | None = None,
        topic_id: int | None = None,
    ) -> tuple[list[News], int]:
        """获取新闻列表 - 使用预加载优化"""
        with track_query("news_get_list", get_query_optimizer()):
            query = select(News)
            count_query = select(func.count(News.id))

        if topic_id is not None:
            query = query.join(
                NewsTopicItem, NewsTopicItem.news_id == News.id).where(
                NewsTopicItem.topic_id == topic_id)
            count_query = (
                select(func.count(func.distinct(News.id)))
                .select_from(News)
                .join(NewsTopicItem, NewsTopicItem.news_id == News.id)
                .where(NewsTopicItem.topic_id == topic_id)
            )

        if category:
            query = query.where(News.category == category)
            count_query = count_query.where(News.category == category)

        if keyword:
            pattern = f"%{self._escape_like(keyword)}%"
            query = query.where(
                or_(
                    News.title.ilike(pattern),
                    News.summary.ilike(pattern),
                    News.content.ilike(pattern),
                )
            )
            count_query = count_query.where(
                or_(
                    News.title.ilike(pattern),
                    News.summary.ilike(pattern),
                    News.content.ilike(pattern),
                )
            )

        if from_dt:
            query = query.where(News.published_at >= from_dt)
            count_query = count_query.where(News.published_at >= from_dt)

        if to_dt:
            query = query.where(News.published_at <= to_dt)
            count_query = count_query.where(News.published_at <= to_dt)

        if published_only:
            query = query.where(News.is_published)
            query = query.where(
                or_(News.review_status == "approved", News.review_status is None))
            count_query = count_query.where(News.is_published)
            count_query = count_query.where(
                or_(News.review_status == "approved", News.review_status is None))

        if review_status:
            query = query.where(News.review_status == review_status)
            count_query = count_query.where(
                News.review_status == review_status)

        if ai_risk_level:
            query = query.where(
                News.ai_risk_level == ai_risk_level)  # pyright: ignore
            count_query = count_query.where(
                News.ai_risk_level == ai_risk_level)  # pyright: ignore

        if source_site:
            query = query.where(News.source_site == source_site)
            count_query = count_query.where(News.source_site == source_site)

        if source:
            query = query.where(News.source == source)
            count_query = count_query.where(News.source == source)

        if is_top is not None:
            query = query.where(News.is_top == is_top)
            count_query = count_query.where(News.is_top == is_top)

            query = query.order_by(desc(News.published_at))

            query = query.offset((page - 1) * page_size).limit(page_size)

            # 应用预加载优化 - 使用 selectinload 预加载 AI 标注信息
            query = apply_news_preload(query, level="basic")

            result = await db.execute(query)
            items = list(result.scalars().all())

            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0

            return items, total

    async def update(
        self,
        db: AsyncSession,
        news: News,
        news_data: NewsUpdate,
        *,
        admin_user_id: int | None = None,
        change_desc: str | None = None,
    ) -> News:
        """更新新闻"""
        old_snapshot = self._snapshot_json(news)

        update_data = news_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(news, field, value)

        if news.is_published and not news.published_at:
            news.published_at = datetime.now()

        db.add(news)
        await db.flush()

        new_snapshot = self._snapshot_json(news)
        if old_snapshot != new_snapshot:
            version = NewsVersion(
                news_id=news.id,
                version=news.versions_count +
                1 if hasattr(news, "versions_count") else 1,  # pyright: ignore
                snapshot=new_snapshot,
                change_desc=change_desc or "更新",
                created_by=admin_user_id,
            )
            db.add(version)

        await db.commit()
        await db.refresh(news)
        return news

    async def list_versions(
        self, db: AsyncSession, news_id: int, *, limit: int = 50
    ) -> list[NewsVersion]:
        """获取新闻版本列表"""
        result = await db.execute(
            select(NewsVersion)
            .where(NewsVersion.news_id == news_id)
            .order_by(NewsVersion.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_version_by_id(
            self, db: AsyncSession, version_id: int) -> NewsVersion | None:
        """根据ID获取版本"""
        result = await db.execute(select(NewsVersion).where(NewsVersion.id == version_id))
        return result.scalar_one_or_none()

    async def rollback_to_version(
        self,
        db: AsyncSession,
        news: News,
        version: NewsVersion,
        *,
        admin_user_id: int | None = None,
    ) -> News:
        """回滚到指定版本"""
        try:
            snapshot_data = json.loads(version.snapshot_json)
        except (json.JSONDecodeError, TypeError):
            raise ValueError("无效的版本快照")

        news.title = snapshot_data.get("title", news.title)
        news.summary = snapshot_data.get("summary", news.summary)
        news.content = snapshot_data.get("content", news.content)
        news.cover_image = snapshot_data.get("cover_image", news.cover_image)
        news.category = snapshot_data.get("category", news.category)
        news.source = snapshot_data.get("source", news.source)
        news.source_url = snapshot_data.get("source_url", news.source_url)
        news.source_site = snapshot_data.get("source_site", news.source_site)
        news.author = snapshot_data.get("author", news.author)
        news.is_top = snapshot_data.get("is_top", news.is_top)

        new_snapshot = self._snapshot_json(news)

        version = NewsVersion(
            news_id=news.id,
            action=f"rollback_to_{version.id if version else 'initial'}",
            snapshot_json=new_snapshot,
            reason=f"回滚到版本 {version.id if version else 'initial'}",
            created_by=admin_user_id,
        )

        db.add(version)
        await db.commit()
        await db.refresh(news)
        return news

    async def process_scheduled_news(
            self, db: AsyncSession, batch_size: int = 50) -> tuple[int, int]:
        """处理定时发布的新闻"""
        now = datetime.now()

        pending_news = await db.execute(
            select(News)
            .where(
                News.scheduled_publish_at is not None,
                News.scheduled_publish_at <= now,
                News.is_published == False,
                News.review_status == "approved",
            )
            .limit(batch_size)
        )
        news_list = list(pending_news.scalars().all())

        published_count = 0
        skipped_count = 0

        for news in news_list:
            if news.scheduled_unpublish_at and news.scheduled_unpublish_at <= now:
                skipped_count += 1
                continue

            news.is_published = True
            news.published_at = now
            db.add(news)
            published_count += 1

        await db.commit()
        return published_count, skipped_count

    async def delete(self, db: AsyncSession, news: News) -> None:
        """删除新闻"""
        await db.delete(news)
        await db.commit()

    async def increment_view(self, db: AsyncSession, news: News) -> None:
        """增加浏览量"""
        news.view_count = (news.view_count or 0) + 1
        db.add(news)
        await db.commit()

    async def record_view_history(
            self, db: AsyncSession, news_id: int, user_id: int) -> None:
        """记录浏览历史"""
        if user_id:
            db_entry = NewsViewHistory(news_id=news_id, user_id=user_id)
            db.add(db_entry)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()

    async def get_user_history(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[News], int]:
        """获取用户浏览历史"""
        query = (
            select(NewsViewHistory)
            .where(NewsViewHistory.user_id == user_id)
            .order_by(NewsViewHistory.viewed_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        history = await db.execute(query)
        history_list = list(history.scalars().all())

        news_ids = [h.news_id for h in history_list]

        if not news_ids:
            return [], 0

        news_query = select(News).where(News.id.in_(news_ids))
        news_result = await db.execute(news_query)
        news_items = {n.id: n for n in news_result.scalars().all()}

        ordered_news = [news_items[nid]
                        for nid in news_ids if nid in news_items]

        count_query = select(
            func.count(
                NewsViewHistory.id)).where(
            NewsViewHistory.user_id == user_id)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return ordered_news, total

    async def toggle_favorite(
        self, db: AsyncSession, news_id: int, user_id: int
    ) -> tuple[bool, int]:
        """切换收藏状态"""
        result = await db.execute(
            select(NewsFavorite).where(
                NewsFavorite.news_id == news_id, NewsFavorite.user_id == user_id
            )
        )
        favorite = result.scalar_one_or_none()

        if favorite:
            await db.delete(favorite)
            await db.commit()
            return False, 0

        favorite = NewsFavorite(news_id=news_id, user_id=user_id)
        db.add(favorite)
        await db.commit()

        count_result = await db.execute(
            select(
                func.count(
                    NewsFavorite.id)).where(
                NewsFavorite.news_id == news_id)
        )
        count = count_result.scalar() or 0

        return True, count

    async def is_favorited(self, db: AsyncSession,
                           news_id: int, user_id: int) -> bool:
        """检查是否已收藏"""
        result = await db.execute(
            select(NewsFavorite).where(
                NewsFavorite.news_id == news_id, NewsFavorite.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_favorite_count(self, db: AsyncSession, news_id: int) -> int:
        """获取收藏数量"""
        result = await db.execute(
            select(
                func.count(
                    NewsFavorite.id)).where(
                NewsFavorite.news_id == news_id)
        )
        return result.scalar() or 0

    async def get_favorite_counts(
            self, db: AsyncSession, news_ids: Sequence[int]) -> dict[int, int]:
        """批量获取收藏数量"""
        if not news_ids:
            return {}

        result = await db.execute(
            select(NewsFavorite.news_id, func.count(NewsFavorite.id))
            .where(NewsFavorite.news_id.in_(news_ids))
            .group_by(NewsFavorite.news_id)
        )
        return {row[0]: int(row[1]) for row in result.all()}

    async def get_favorite_stats(
        self,
        db: AsyncSession,
        news_ids: Sequence[int],
        user_id: int | None = None,
    ) -> dict[int, tuple[int, bool]]:
        """获取收藏统计（兼容旧接口）"""
        ids = [int(i) for i in news_ids]
        if not ids:
            return {}

        if user_id is None:
            result = await db.execute(
                select(NewsFavorite.news_id, func.count(NewsFavorite.id))
                .where(NewsFavorite.news_id.in_(ids))
                .group_by(NewsFavorite.news_id)
            )
            return {row[0]: (int(row[1]), False) for row in result.all()}

        user_favorites = await self.get_favorited_news_ids(db, user_id)
        user_favorite_set = set(user_favorites)

        result = await db.execute(
            select(NewsFavorite.news_id, func.count(NewsFavorite.id))
            .where(NewsFavorite.news_id.in_(ids))
            .group_by(NewsFavorite.news_id)
        )

        stats = {}
        for row in result.all():
            news_id = row[0]
            count = int(row[1])
            is_favorited = news_id in user_favorite_set
            stats[news_id] = (count, is_favorited)

        return stats  # pyright: ignore

    async def get_favorited_news_ids(
            self, db: AsyncSession, user_id: int) -> list[int]:
        """获取用户收藏的新闻ID"""
        result = await db.execute(
            select(NewsFavorite.news_id)
            .where(NewsFavorite.user_id == user_id)
            .order_by(NewsFavorite.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_favorites(
        self,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[News], int]:
        """获取用户收藏的新闻"""
        query = (
            select(News)
            .join(NewsFavorite, News.id == NewsFavorite.news_id)
            .where(NewsFavorite.user_id == user_id)
            .order_by(NewsFavorite.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        news_list = list(result.scalars().all())

        count_result = await db.execute(
            select(
                func.count(
                    NewsFavorite.id)).where(
                NewsFavorite.user_id == user_id)
        )
        total = count_result.scalar() or 0

        return news_list, total

    async def get_categories(
            self, db: AsyncSession) -> list[dict[str, object]]:
        """获取新闻分类统计"""
        result = await db.execute(
            select(
                News.category,
                func.count(News.id).label("count"),
                func.sum(case((News.is_published, 1), else_=0)
                         ).label("published_count"),
            )
            .where(News.category is not None, News.category != "")
            .group_by(News.category)
            .order_by(desc(func.count(News.id)))
        )
        return [
            {"category": str(row[0] or ""), "count": int(
                row[1] or 0), "published_count": int(row[2] or 0)}
            for row in result.all()
        ]

    async def get_hot_news(
        self,
        db: AsyncSession,
        days: int = 7,
        limit: int = 10,
        category: str | None = None,
    ) -> list[News]:
        """获取热门新闻"""
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=days)
        query = (
            select(News)
            .where(
                News.is_published,
                News.published_at >= start_date,
                or_(News.review_status == "approved",
                    News.review_status is None),
            )
            .order_by(desc(News.view_count), desc(News.published_at))
            .limit(limit)
        )

        if category:
            query = query.where(News.category == category)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_top_news(self, db: AsyncSession,
                           limit: int = 5) -> list[News]:
        """获取置顶新闻"""
        result = await db.execute(
            select(News)
            .where(
                News.is_top,
                News.is_published,
                or_(News.review_status == "approved",
                    News.review_status is None),
            )
            .order_by(desc(News.published_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_news(self, db: AsyncSession,
                              limit: int = 10) -> list[News]:
        """获取最新新闻"""
        result = await db.execute(
            select(News)
            .where(
                News.is_published,
                or_(News.review_status == "approved",
                    News.review_status is None),
            )
            .order_by(desc(News.published_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_related_news(
        self, db: AsyncSession, news_id: int, limit: int = 5
    ) -> list[News]:
        """获取相关新闻"""
        news = await self.get_by_id(db, news_id)
        if not news or not news.category:
            return []

        result = await db.execute(
            select(News)
            .where(
                News.id != news_id,
                News.category == news.category,
                News.is_published,
                or_(News.review_status == "approved",
                    News.review_status is None),
            )
            .order_by(desc(News.published_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_ai_keywords(self, db: AsyncSession,
                              news_ids: list[int]) -> dict[int, list[str]]:
        """获取AI关键词"""
        import json
        from ...models.news_ai import NewsAIAnnotation
        ids = [int(i) for i in news_ids]
        if not ids:
            return {}
        res = await db.execute(
            select(NewsAIAnnotation.news_id, NewsAIAnnotation.keywords).where(
                NewsAIAnnotation.news_id.in_(ids)
            )
        )
        rows = list(res.all())
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
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        for x in parsed:  # pyright: ignore
                            s = str(x or "").strip()  # pyright: ignore
                            if s:
                                kws.append(s)
            except Exception:
                kws = []
            out[int(nid)] = kws
        return out

    async def get_recommended_news(
        self,
        db: AsyncSession,
        user_id: int | None,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        keyword: str | None = None,
        ai_risk_level: str | None = None,
        source_site: str | None = None,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> tuple[list[News], int]:
        """获取推荐新闻（复用列表逻辑）"""
        return await self.get_list(
            db, page, page_size, category, keyword,
            published_only=True, ai_risk_level=ai_risk_level,
            source_site=source_site, from_dt=from_dt, to_dt=to_dt
        )

    async def notify_subscribers_on_publish(
            self, db: AsyncSession, news: News) -> int:
        """发布时通知订阅者"""
        return await news_subscription_service.notify_subscribers_on_publish(db, news)

    async def invalidate_hot_cache(self) -> None:
        """使热门新闻缓存失效"""
        self._hot_cache.clear()

    async def review_news_admin(
        self,
        db: AsyncSession,
        news_id: int,
        action: str,
        reason: str | None = None,
        *,
        admin_user_id: int | None = None,
    ) -> News | None:
        """审核新闻（管理员）"""
        news = await self.get_by_id(db, news_id)
        if not news:
            return None
        return await self._review_news(db, news, action, reason, admin_user_id=admin_user_id)

    async def _review_news(
        self,
        db: AsyncSession,
        news: News,
        action: str,
        reason: str | None = None,
        *,
        admin_user_id: int | None = None,
    ) -> News:
        """内部审核逻辑"""
        from ...models.news_workbench import NewsVersion
        old_status = news.review_status
        news.review_status = action
        news.review_reason = reason
        news.reviewed_at = datetime.now()
        news.reviewed_by = admin_user_id  # pyright: ignore

        if action == "approved":
            if not news.is_published:
                if news.scheduled_publish_at:
                    if news.scheduled_publish_at <= datetime.now():
                        news.is_published = True
                        news.published_at = datetime.now()
                else:
                    news.is_published = True
                    news.published_at = datetime.now()
        else:
            news.is_published = False

        db.add(news)
        await db.flush()

        if old_status != action:
            version = NewsVersion(
                news_id=news.id,
                version=news.versions_count +
                1 if hasattr(news, "versions_count") else 1,  # pyright: ignore
                snapshot=self._snapshot_json(news),
                change_desc=f"审核: {action}",
                created_by=admin_user_id,
            )
            db.add(version)

        await db.commit()
        await db.refresh(news)
        return news

    async def get_comments(
        self, db: AsyncSession, news_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[NewsComment], int]:
        """获取评论列表"""
        return await news_comment_service.get_comments(db, news_id, page, page_size)

    async def create_comment(
        self, db: AsyncSession, news_id: int, user_id: int, content: str,
        review_status: str = "approved", review_reason: str | None = None
    ) -> NewsComment:
        """创建评论"""
        from ...models.news import NewsComment
        comment = NewsComment(
            news_id=news_id,
            user_id=user_id,
            content=content,
            review_status=review_status,
            review_reason=review_reason,
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment

    async def get_comment(self, db: AsyncSession,
                          comment_id: int) -> NewsComment | None:
        """获取评论"""
        return await news_comment_service.get_comment(db, comment_id)

    async def delete_comment(self, db: AsyncSession,
                             comment: NewsComment) -> None:
        """删除评论"""
        await news_comment_service.delete_comment(db, comment)

    async def list_comments_admin(
        self, db: AsyncSession, page: int = 1, page_size: int = 20,
        review_status: str | None = None, news_id: int | None = None,
        user_id: int | None = None, keyword: str | None = None,
        include_deleted: bool = False
    ) -> tuple[list[NewsComment], int]:
        """管理后台评论列表"""
        query = select(NewsComment)
        count_query = select(func.count(NewsComment.id))

        conditions = []
        if review_status:
            conditions.append(NewsComment.review_status ==
                              review_status)  # pyright: ignore
        if news_id is not None:
            conditions.append(
                NewsComment.news_id == news_id)  # pyright: ignore
        if user_id is not None:
            conditions.append(
                NewsComment.user_id == user_id)  # pyright: ignore
        if keyword:
            pattern = f"%{keyword}%"
            conditions.append(
                NewsComment.content.ilike(pattern))  # pyright: ignore
        if not include_deleted:
            conditions.append(NewsComment.is_deleted ==
                              False)  # pyright: ignore

        if conditions:
            query = query.where(and_(*conditions))  # pyright: ignore
            count_query = count_query.where(
                and_(*conditions))  # pyright: ignore

        query = query.order_by(
            NewsComment.created_at.desc()).offset(
            (page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        comments = list(result.scalars().all())

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return comments, total

    async def review_comment_admin(
            self,
            db: AsyncSession,
            comment_id: int,
            action: str,
            reason: str | None = None,
            admin_user_id: int | None = None) -> NewsComment | None:
        """审核评论（管理员）"""
        comment = await news_comment_service.get_comment(db, comment_id)
        if not comment:
            return None
        return await news_comment_service.review_comment_admin(db, comment, action, reason)

    async def list_subscriptions(
            self, db: AsyncSession, user_id: int) -> list[NewsSubscription]:
        """获取用户订阅列表"""
        return await news_subscription_service.list_subscriptions(db, user_id)

    async def create_subscription(
        self, db: AsyncSession, user_id: int, sub_type: str, value: str
    ) -> NewsSubscription:
        """创建订阅"""
        if sub_type == "category":
            return await news_subscription_service.create_subscription(db, user_id, category=value)
        return await news_subscription_service.create_subscription(db, user_id, keywords=value)

    async def delete_subscription(
            self, db: AsyncSession, user_id: int, sub_id: int) -> bool:
        """删除订阅"""
        return await news_subscription_service.delete_subscription(db, user_id, sub_id)

    async def get_subscribed_news(
        self, db: AsyncSession, user_id: int, page: int = 1, page_size: int = 20,
        category: str | None = None, keyword: str | None = None,
        ai_risk_level: str | None = None, source_site: str | None = None,
        from_dt: datetime | None = None, to_dt: datetime | None = None
    ) -> tuple[list[News], int]:
        """获取订阅的新闻"""
        news_list, total = await news_subscription_service.get_subscribed_news(db, user_id, page, page_size)
        return news_list, total


# 单例
_news_service: NewsService | None = None


def get_news_service() -> NewsService:
    """获取新闻服务实例"""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service


news_service = get_news_service()
