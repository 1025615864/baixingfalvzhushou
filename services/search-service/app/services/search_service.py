"""搜索服务 - 服务层"""
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

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
        query: str,
        search_type: str = "all",
        page: int = 1,
        page_size: int = 20,
    ) -> Dict:
        """全局搜索（聚合多服务数据）"""
        items: List[SearchItem] = []

        # 这里应该调用各微服务的搜索接口
        # 当前使用模拟数据作为占位
        if search_type in ("all", "news"):
            items.extend(await self._search_news(query, page_size))

        if search_type in ("all", "post"):
            items.extend(await self._search_posts(query, page_size))

        if search_type in ("all", "lawyer"):
            items.extend(await self._search_lawyers(query, page_size))

        if search_type in ("all", "knowledge"):
            items.extend(await self._search_knowledge(query, page_size))

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = items[start:end]

        return {
            "items": [item.__dict__ for item in paginated],
            "total": total,
            "query": query,
            "type": search_type,
        }

    async def get_suggestions(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索建议（自动补全）"""
        base_keywords = [
            "离婚", "劳动", "合同", "工伤", "债务", "房产",
            "继承", "交通事故", "医疗纠纷", "刑事",
        ]

        suggestions = [
            {"text": kw, "count": 1000 - i * 50}
            for i, kw in enumerate(base_keywords)
            if query.lower() in kw.lower()
        ][:limit]

        if not suggestions and len(query) >= 2:
            suggestions = [
                {"text": query + suffix, "count": 100}
                for suffix in ["相关", "律师", "咨询", "服务"]
            ][:limit]

        return suggestions

    async def get_hot_searches(self, limit: int = 10) -> List[Dict]:
        """热门搜索"""
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
