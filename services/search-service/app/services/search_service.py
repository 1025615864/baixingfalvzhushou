"""搜索服务 - 服务层"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SearchIndex, HotSearch, SearchLog

logger = logging.getLogger(__name__)


@dataclass
class SearchItem:
    id: int
    type: str
    title: str
    description: str
    url: str
    score: float = 1.0


class SearchService:
    """搜索服务 - 跨服务聚合搜索"""

    async def search_all(
        self,
        session: AsyncSession,
        query: str,
        search_type: str = "all",
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None,
    ) -> Dict:
        """全局搜索（聚合多服务数据）"""
        items: List[SearchItem] = []

        # 从搜索索引中查询
        items.extend(await self._search_from_index(session, query, search_type, page_size))

        # 如果没有足够结果，使用占位数据
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

        # 记录搜索日志
        if user_id:
            await self.record_search(session, user_id, query, search_type, total)

        return {
            "items": [item.__dict__ for item in paginated],
            "total": total,
            "query": query,
            "type": search_type,
        }

    async def _search_from_index(
        self,
        session: AsyncSession,
        query: str,
        search_type: str,
        limit: int,
    ) -> List[SearchItem]:
        """从搜索索引中查询"""
        stmt = select(SearchIndex).where(
            SearchIndex.status == "active",
        )

        if search_type != "all":
            stmt = stmt.where(SearchIndex.item_type == search_type)

        # 简单全文搜索
        stmt = stmt.where(
            SearchIndex.title.ilike(f"%{query}%") |
            SearchIndex.content.ilike(f"%{query}%") |
            SearchIndex.keywords.ilike(f"%{query}%")
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
        """搜索建议（自动补全）"""
        # 从索引中获取建议
        stmt = select(SearchIndex.title).where(
            SearchIndex.status == "active",
            SearchIndex.title.ilike(f"%{query}%"),
        ).distinct().limit(limit)

        result = await session.execute(stmt)
        titles = result.scalars().all()

        suggestions = [{"text": t, "count": 100} for t in titles]

        # 如果没有足够结果，使用关键词建议
        if len(suggestions) < limit and len(query) >= 2:
            base_keywords = [
                "离婚", "劳动", "合同", "工伤", "债务", "房产",
                "继承", "交通事故", "医疗纠纷", "刑事",
            ]
            for kw in base_keywords:
                if query.lower() in kw.lower() and len(suggestions) < limit:
                    suggestions.append({"text": kw, "count": 1000 - base_keywords.index(kw) * 50})

        return suggestions[:limit]

    async def get_hot_searches(self, session: AsyncSession, limit: int = 10) -> List[Dict]:
        """热门搜索"""
        # 从数据库获取热门搜索
        stmt = select(HotSearch).where(
            HotSearch.status == "active",
        ).order_by(
            HotSearch.search_count.desc()
        ).limit(limit)

        result = await session.execute(stmt)
        hot_searches = result.scalars().all()

        if hot_searches:
            return [
                {"keyword": hs.keyword, "count": hs.search_count}
                for hs in hot_searches
            ]

        # 默认热门搜索
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

        return [
            {"keyword": kw, "count": cnt}
            for kw, cnt in hot_keywords[:limit]
        ]

    async def record_search(
        self,
        session: AsyncSession,
        user_id: int,
        query: str,
        search_type: str = "all",
        result_count: int = 0,
    ) -> SearchLog:
        """记录搜索日志"""
        log = SearchLog(
            user_id=user_id,
            query=query,
            search_type=search_type,
            result_count=result_count,
        )
        session.add(log)
        await session.flush()

        # 更新热门搜索
        await self._update_hot_search(session, query)

        return log

    async def _update_hot_search(self, session: AsyncSession, keyword: str):
        """更新热门搜索计数"""
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

    async def _search_news(self, query: str, limit: int) -> List[SearchItem]:
        """搜索新闻（占位）"""
        return [
            SearchItem(
                id=i,
                type="news",
                title=f"新闻: {query}",
                description=f"关于{query}的最新新闻",
                url=f"/news/{i}",
                score=0.9,
            )
            for i in range(1, min(limit + 1, 4))
        ]

    async def _search_posts(self, query: str, limit: int) -> List[SearchItem]:
        """搜索帖子（占位）"""
        return [
            SearchItem(
                id=i,
                type="post",
                title=f"帖子: {query}",
                description=f"关于{query}的社区讨论",
                url=f"/forum/{i}",
                score=0.8,
            )
            for i in range(1, min(limit + 1, 4))
        ]

    async def _search_lawyers(self, query: str, limit: int) -> List[SearchItem]:
        """搜索律师（占位）"""
        return [
            SearchItem(
                id=i,
                type="lawyer",
                title=f"律师: {query}",
                description=f"擅长{query}领域的律师",
                url=f"/lawyer/{i}",
                score=0.85,
            )
            for i in range(1, min(limit + 1, 4))
        ]

    async def _search_knowledge(self, query: str, limit: int) -> List[SearchItem]:
        """搜索法律知识（占位）"""
        return [
            SearchItem(
                id=i,
                type="knowledge",
                title=f"法律知识: {query}",
                description=f"关于{query}的法律知识",
                url=f"/knowledge/{i}",
                score=0.95,
            )
            for i in range(1, min(limit + 1, 4))
        ]


search_service = SearchService()
