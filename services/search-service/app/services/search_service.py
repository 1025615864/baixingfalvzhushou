import logging
from typing import List, Dict, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SearchIndex, HotSearch, SearchLog, SearchItem
from app.services.cache_service import cache_service
from app.services.client_service import client_service
from app.config.settings import settings

logger = logging.getLogger(__name__)


class SearchService:

    async def search_all(
        self,
        session: AsyncSession,
        query: str,
        search_type: str = "all",
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None,
    ) -> Dict:
        cache_key = f"search:{search_type}:{query}:{page}:{page_size}"
        cached = await cache_service.get_json(cache_key)
        if cached is not None:
            if user_id:
                await self.record_search(session, user_id, query, search_type, cached.get("total", 0))
            return cached

        items: List[SearchItem] = []

        items.extend(await self._search_from_index(session, query, search_type, page_size))

        if len(items) < page_size:
            if search_type in ("all", "news"):
                items.extend(await self._search_news(query, page_size - len(items)))

            if search_type in ("all", "post"):
                items.extend(await self._search_posts(query, page_size - len(items)))

            if search_type in ("all", "lawyer"):
                items.extend(await self._search_lawyers(query, page_size - len(items)))

            if search_type in ("all", "knowledge"):
                items.extend(await self._search_knowledge(query, page_size - len(items)))

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = items[start:end]

        if user_id:
            await self.record_search(session, user_id, query, search_type, total)

        result = {
            "items": [item.__dict__ for item in paginated],
            "total": total,
            "query": query,
            "type": search_type,
        }

        await cache_service.set_json(cache_key, result, settings.SEARCH_CACHE_TTL)

        return result

    async def search_by_type(
        self,
        session: AsyncSession,
        item_type: str,
        query: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict:
        cache_key = f"search:type:{item_type}:{query}:{page}:{page_size}"
        cached = await cache_service.get_json(cache_key)
        if cached is not None:
            return cached

        items: List[SearchItem] = []

        index_items = await self._search_from_index(session, query, item_type, page_size)
        items.extend(index_items)

        if len(items) < page_size:
            remaining = page_size - len(items)
            type_methods = {
                "news": self._search_news,
                "post": self._search_posts,
                "lawyer": self._search_lawyers,
                "knowledge": self._search_knowledge,
            }
            method = type_methods.get(item_type)
            if method:
                items.extend(await method(query, remaining))

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = items[start:end]

        result = {
            "items": [item.__dict__ for item in paginated],
            "total": total,
            "query": query,
            "type": item_type,
        }

        await cache_service.set_json(cache_key, result, settings.SEARCH_CACHE_TTL)

        return result

    async def get_search_history(
        self,
        session: AsyncSession,
        user_id: int,
        limit: int = 20,
    ) -> List[Dict]:
        cache_key = f"search:history:{user_id}:{limit}"
        cached = await cache_service.get_json(cache_key)
        if cached is not None:
            return cached

        stmt = select(SearchLog).where(
            SearchLog.user_id == user_id,
        ).order_by(
            SearchLog.created_at.desc()
        ).limit(limit)

        result = await session.execute(stmt)
        logs = result.scalars().all()

        history = [
            {
                "query": log.query,
                "type": log.search_type,
                "result_count": log.result_count,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

        await cache_service.set_json(cache_key, history, settings.SEARCH_CACHE_TTL)

        return history

    async def _search_from_index(
        self,
        session: AsyncSession,
        query: str,
        search_type: str,
        limit: int,
    ) -> List[SearchItem]:
        stmt = select(SearchIndex).where(
            SearchIndex.status == "active",
        )

        if search_type != "all":
            stmt = stmt.where(SearchIndex.item_type == search_type)

        search_tsquery = func.plainto_tsquery('simple', query)
        stmt = stmt.where(
            or_(
                SearchIndex.search_vector.op('@@')(search_tsquery),
                SearchIndex.title.ilike(f"%{query}%"),
            )
        ).order_by(
            func.ts_rank(SearchIndex.search_vector, search_tsquery).desc()
        )

        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        indices = result.scalars().all()

        return [
            SearchItem(
                id=idx.item_id,
                type=idx.item_type,
                title=idx.title,
                description=idx.content[:200] if idx.content else "",
                url=f"/{idx.item_type}/{idx.item_id}",
                score=1.0,
            )
            for idx in indices
        ]

    async def get_suggestions(self, session: AsyncSession, query: str, limit: int = 10) -> List[Dict]:
        cache_key = f"search:suggestions:{query}:{limit}"
        cached = await cache_service.get_json(cache_key)
        if cached is not None:
            return cached

        stmt = select(SearchIndex.title).where(
            SearchIndex.status == "active",
            SearchIndex.title.ilike(f"%{query}%"),
        ).distinct().limit(limit)

        result = await session.execute(stmt)
        titles = result.scalars().all()

        suggestions = [{"text": t, "count": 100} for t in titles]

        if len(suggestions) < limit and len(query) >= 2:
            base_keywords = [
                "离婚", "劳动", "合同", "工伤", "债务", "房产",
                "继承", "交通事故", "医疗纠纷", "刑事",
            ]
            for kw in base_keywords:
                if query.lower() in kw.lower() and len(suggestions) < limit:
                    suggestions.append({"text": kw, "count": 1000 - base_keywords.index(kw) * 50})

        suggestions = suggestions[:limit]
        await cache_service.set_json(cache_key, suggestions, settings.SEARCH_CACHE_TTL)
        return suggestions

    async def get_hot_searches(self, session: AsyncSession, limit: int = 10) -> List[Dict]:
        cache_key = f"search:hot:{limit}"
        cached = await cache_service.get_json(cache_key)
        if cached is not None:
            return cached

        stmt = select(HotSearch).where(
            HotSearch.status == "active",
        ).order_by(
            HotSearch.search_count.desc()
        ).limit(limit)

        result = await session.execute(stmt)
        hot_searches = result.scalars().all()

        if hot_searches:
            items = [
                {"keyword": hs.keyword, "count": hs.search_count}
                for hs in hot_searches
            ]
        else:
            hot_keywords = [
                ("离婚程序", 15230),
                ("劳动合同法", 12450),
                ("工伤认定", 11200),
                ("房屋买卖合同", 9850),
                ("债务纠纷", 8900),
                ("交通事故处理", 7650),
                ("遗产继承", 6540),
                ("医疗事故鉴定", 5430),
                ("刑事拘留", 4320),
                ("劳动仲裁", 3210),
            ]
            items = [
                {"keyword": kw, "count": cnt}
                for kw, cnt in hot_keywords[:limit]
            ]

        await cache_service.set_json(cache_key, items, settings.HOT_SEARCH_CACHE_TTL)
        return items

    async def record_search(
        self,
        session: AsyncSession,
        user_id: int,
        query: str,
        search_type: str = "all",
        result_count: int = 0,
    ) -> SearchLog:
        log = SearchLog(
            user_id=user_id,
            query=query,
            search_type=search_type,
            result_count=result_count,
        )
        session.add(log)
        await session.flush()

        await self._update_hot_search(session, query)

        await cache_service.delete(f"search:history:{user_id}:20")

        return log

    async def _update_hot_search(self, session: AsyncSession, keyword: str):
        stmt = select(HotSearch).where(HotSearch.keyword == keyword)
        result = await session.execute(stmt)
        hot_search = result.scalar_one_or_none()

        if hot_search:
            hot_search.search_count += 1
        else:
            hot_search = HotSearch(
                keyword=keyword,
                search_count=1,
            )
            session.add(hot_search)

        await session.flush()

        await cache_service.delete("search:hot:10")

    async def update_search_vector(self, db: AsyncSession, item_id: int) -> None:
        from sqlalchemy import update
        stmt = (
            update(SearchIndex)
            .where(SearchIndex.id == item_id)
            .values(
                search_vector=func.to_tsvector(
                    'simple',
                    func.coalesce(SearchIndex.title, '') + ' ' + func.coalesce(SearchIndex.content, '')
                )
            )
        )
        await db.execute(stmt)
        await db.commit()

    async def index_document(
        self,
        db: AsyncSession,
        item_type: str,
        item_id: int,
        title: str,
        content: str = "",
        keywords: str = "",
    ) -> SearchIndex:
        index = SearchIndex(
            item_type=item_type,
            item_id=item_id,
            title=title,
            content=content,
            keywords=keywords,
            search_vector=func.to_tsvector('simple', f"{title} {content}"),
        )
        db.add(index)
        await db.commit()
        await db.refresh(index)
        return index

    async def _search_news(self, query: str, limit: int) -> List[SearchItem]:
        try:
            return await client_service.search_news(query, limit)
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return []

    async def _search_posts(self, query: str, limit: int) -> List[SearchItem]:
        try:
            return await client_service.search_posts(query, limit)
        except Exception as e:
            logger.error(f"Error searching posts: {e}")
            return []

    async def _search_lawyers(self, query: str, limit: int) -> List[SearchItem]:
        try:
            return await client_service.search_lawyers(query, limit)
        except Exception as e:
            logger.error(f"Error searching lawyers: {e}")
            return []

    async def _search_knowledge(self, query: str, limit: int) -> List[SearchItem]:
        try:
            return await client_service.search_knowledge(query, limit)
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []


search_service = SearchService()
