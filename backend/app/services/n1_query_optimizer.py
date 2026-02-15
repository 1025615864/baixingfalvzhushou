"""N+1查询优化工具

检测和优化N+1查询问题。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload


class N1QueryDetector:
    """N+1查询检测器"""

    def __init__(self) -> None:
        self.query_count: int = 0
        self.n1_queries: list[dict[str, Any]] = []

    def detect_n1_queries(
        self,
        query_func: callable,
        *args: Any,
        **kwargs: Any
    ) -> dict[str, Any]:
        """检测N+1查询

        Args:
            query_func: 查询函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            检测结果
        """
        import time

        start_time = time.time()
        self.query_count = 0
        self.n1_queries = []

        # 执行查询
        result = query_func(*args, **kwargs)

        duration = time.time() - start_time

        return {
            "result": result,
            "query_count": self.query_count,
            "n1_queries": self.n1_queries,
            "duration_ms": duration * 1000,
        }

    def optimize_with_selectinload(
        self,
        model: Any,
        relationship: str
    ) -> Any:
        """使用selectinload优化

        Args:
            model: 模型类
            relationship: 关系名称

        Returns:
            优化后的查询
        """
        return select(model).options(selectinload(getattr(model, relationship)))

    def optimize_with_joinedload(
        self,
        model: Any,
        relationship: str
    ) -> Any:
        """使用joinedload优化

        Args:
            model: 模型类
            relationship: 关系名称

        Returns:
            优化后的查询
        """
        return select(model).options(joinedload(getattr(model, relationship)))


# 全局N+1查询检测器
n1_detector = N1QueryDetector()


def optimize_news_query() -> dict[str, Any]:
    """优化新闻查询（示例）

    Returns:
        优化结果
    """
    from app.models.news import News

    # 原始查询（可能导致N+1）
    # news_list = await session.execute(select(News).limit(10))
    # for news in news_list.scalars():
    #     # 这里会触发N+1查询
    #     author = news.author

    # 优化后的查询
    optimized_query = n1_detector.optimize_with_selectinload(News, "author")

    return {
        "optimized_query": optimized_query,
        "optimization_type": "selectinload",
        "relationship": "author",
    }


def optimize_forum_post_query() -> dict[str, Any]:
    """优化论坛帖子查询（示例）

    Returns:
        优化结果
    """
    from app.models.forum.posts import Post

    # 原始查询（可能导致N+1）
    # posts = await session.execute(select(Post).limit(10))
    # for post in posts.scalars():
    #     # 这里会触发N+1查询
    #     author = post.author
    #     comments = post.comments

    # 优化后的查询
    optimized_query = n1_detector.optimize_with_joinedload(Post, "author")

    return {
        "optimized_query": optimized_query,
        "optimization_type": "joinedload",
        "relationship": "author",
    }


# N+1查询优化最佳实践
N1_OPTIMIZATION_BEST_PRACTICES = {
    "selectinload": {
        "use_case": "一对多关系，需要加载所有关联对象",
        "example": "新闻列表加载作者信息",
        "performance": "中等（2-3次查询）",
    },
    "joinedload": {
        "use_case": "一对一关系，需要加载关联对象",
        "example": "帖子加载作者信息",
        "performance": "好（1次查询）",
    },
    "lazyload": {
        "use_case": "延迟加载，只在需要时加载",
        "example": "用户详情页加载订单列表",
        "performance": "差（N+1查询）",
    },
    "subqueryload": {
        "use_case": "多对多关系，需要加载关联对象",
        "example": "用户加载权限列表",
        "performance": "中等（2次查询）",
    },
}


def get_optimization_suggestions(
    query_type: str = "select"
) -> list[dict[str, Any]]:
    """获取优化建议

    Args:
        query_type: 查询类型

    Returns:
        优化建议列表
    """
    suggestions = []

    if query_type == "select":
        suggestions.append({
            "strategy": "selectinload",
            "description": "使用selectinload预加载一对多关系",
            "benefit": "减少查询次数，提高性能",
            "example": "select(News).options(selectinload(News.author))",
        })

        suggestions.append({
            "strategy": "joinedload",
            "description": "使用joinedload预加载一对一关系",
            "benefit": "一次查询加载所有数据",
            "example": "select(Post).options(joinedload(Post.author))",
        })

    return suggestions
