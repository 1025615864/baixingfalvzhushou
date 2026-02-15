"""搜索建议服务

提供搜索建议和热门关键词功能
"""
from ...models.system import SearchHistory
import logging
from typing import cast
from typing_extensions import TypedDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as future_select

logger = logging.getLogger(__name__)

# 延迟导入以避免循环依赖


class HotKeyword(TypedDict):
    keyword: str
    count: int


class SearchSuggestionService:
    """搜索建议服务"""

    @staticmethod
    def _escape_like(value: str, escape: str = "\\") -> str:
        """转义 LIKE 查询的特殊字符"""
        s = str(value or "")
        if not escape:
            return s
        s = s.replace(escape, escape + escape)
        s = s.replace("%", escape + "%")
        s = s.replace("_", escape + "_")
        return s

    async def get_search_suggestions(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 5
    ) -> list[str]:
        """获取搜索建议

        Args:
            db: 数据库会话
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            搜索建议列表
        """
        from ...models.news import News
        from ...models.forum import Post

        if not query or len(query) < 1:
            return []

        suggestions: list[str] = []
        q = str(query or "")
        search_term = f"{self._escape_like(q)}%"

        # 从新闻标题获取建议
        news_query = select(News.title).where(
            News.title.ilike(search_term, escape="\\"),
            News.is_published
        ).limit(limit)
        news_result = await db.execute(news_query)
        suggestions.extend(cast(list[str], news_result.scalars().all()))

        # 从帖子标题获取建议
        posts_query = select(Post.title).where(
            Post.title.ilike(search_term, escape="\\"),
            Post.is_deleted == False
        ).limit(limit)
        posts_result = await db.execute(posts_query)
        suggestions.extend(cast(list[str], posts_result.scalars().all()))

        # 去重并限制数量（保持顺序）
        seen: set[str] = set()
        unique: list[str] = []
        for s in suggestions:
            if s in seen:
                continue
            seen.add(s)
            unique.append(s)
            if len(unique) >= limit:
                break

        return unique

    async def get_hot_keywords(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> list[HotKeyword]:
        """获取热门搜索关键词

        Args:
            db: 数据库会话
            limit: 返回数量限制

        Returns:
            热门关键词列表
        """
        try:
            query = (
                select(
                    SearchHistory.keyword, func.count(
                        SearchHistory.id).label('count'))
                .group_by(SearchHistory.keyword)
                .order_by(func.count(SearchHistory.id).desc())
                .limit(limit)
            )
            result = await db.execute(query)
            items: list[HotKeyword] = []
            for row in result.all():
                items.append({
                    "keyword": cast(str, row[0]),
                    "count": cast(int, row[1]),
                })
            return items
        except Exception:
            # 如果表不存在，返回默认热词
            return [
                {"keyword": "劳动合同", "count": 100},
                {"keyword": "离婚财产", "count": 85},
                {"keyword": "交通事故", "count": 72},
                {"keyword": "借款纠纷", "count": 65},
                {"keyword": "房屋买卖", "count": 58},
            ]


# 单例实例
search_suggestion_service = SearchSuggestionService()
