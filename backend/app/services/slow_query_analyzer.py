"""慢查询分析工具

识别和分析慢查询，提供优化建议。
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SlowQueryAnalyzer:
    """慢查询分析器"""

    def __init__(self, threshold_ms: float = 100.0) -> None:
        self.threshold_ms = threshold_ms
        self.slow_queries: list[dict[str, Any]] = []
        self.query_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0.0,
            "max_time": 0.0,
            "avg_time": 0.0,
        })

    def record_query(
        self,
        sql: str,
        duration_ms: float,
        params: dict[str, Any] | None = None
    ) -> None:
        """记录查询

        Args:
            sql: SQL语句
            duration_ms: 执行时间（毫秒）
            params: 查询参数
        """
        if duration_ms < self.threshold_ms:
            return

        # 记录慢查询
        self.slow_queries.append({
            "sql": sql,
            "duration_ms": duration_ms,
            "params": params,
            "timestamp": time.time(),
        })

        # 更新统计
        sql_hash = str(hash(sql))
        self.query_stats[sql_hash]["count"] += 1
        self.query_stats[sql_hash]["total_time"] += duration_ms
        self.query_stats[sql_hash]["max_time"] = max(
            self.query_stats[sql_hash]["max_time"],
            duration_ms
        )
        self.query_stats[sql_hash]["avg_time"] = (
            self.query_stats[sql_hash]["total_time"] /
            self.query_stats[sql_hash]["count"]
        )

    def get_slow_queries(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取慢查询列表

        Args:
            limit: 返回数量限制

        Returns:
            慢查询列表
        """
        return sorted(
            self.slow_queries,
            key=lambda x: x["duration_ms"],
            reverse=True
        )[:limit]

    def get_query_stats(self) -> dict[str, dict[str, Any]]:
        """获取查询统计

        Returns:
            查询统计信息
        """
        return dict(self.query_stats)

    def get_optimization_suggestions(self) -> list[dict[str, Any]]:
        """获取优化建议

        Returns:
            优化建议列表
        """
        suggestions = []

        for sql_hash, stats in self.query_stats.items():
            if stats["count"] < 5:  # 只分析执行次数>=5的查询
                continue

            # 找到对应的SQL
            sql: str | None = None
            for query in self.slow_queries:
                if str(hash(query["sql"])) == sql_hash:
                    sql = query["sql"]
                    break

            # 分析SQL并提供建议
            if sql and "SELECT" in sql:
                suggestions.append({
                    "sql": sql,
                    "count": stats["count"],
                    "avg_time_ms": stats["avg_time"],
                    "max_time_ms": stats["max_time"],
                    "suggestions": self._analyze_select_query(sql, stats),
                })

        return suggestions

    def _analyze_select_query(
        self,
        sql: str,
        stats: dict[str, Any]
    ) -> list[str]:
        """分析SELECT查询

        Args:
            sql: SQL语句
            stats: 统计信息

        Returns:
            优化建议列表
        """
        suggestions = []

        # 检查是否缺少索引
        if "WHERE" in sql and "JOIN" not in sql:
            suggestions.append("考虑为WHERE条件添加索引")

        # 检查是否使用了SELECT *
        if "SELECT *" in sql:
            suggestions.append("避免使用SELECT *，只查询需要的字段")

        # 检查是否有多个JOIN
        join_count = sql.count("JOIN")
        if join_count > 3:
            suggestions.append(f"查询包含{join_count}个JOIN，考虑优化查询结构")

        # 检查是否有子查询
        if "SELECT" in sql and sql.count("SELECT") > 1:
            suggestions.append("考虑将子查询改写为JOIN")

        # 检查是否有ORDER BY
        if "ORDER BY" in sql and "LIMIT" not in sql:
            suggestions.append("ORDER BY without LIMIT可能导致全表排序，考虑添加LIMIT")

        # 检查平均执行时间
        if stats["avg_time"] > 1000:
            suggestions.append("平均执行时间超过1秒，需要重点优化")

        return suggestions


# 全局慢查询分析器
slow_query_analyzer = SlowQueryAnalyzer(threshold_ms=100.0)


async def analyze_database_slow_queries(
    session: AsyncSession,
    threshold_ms: float = 100.0
) -> list[dict[str, Any]]:
    """分析数据库慢查询

    Args:
        session: 数据库会话
        threshold_ms: 慢查询阈值（毫秒）

    Returns:
        慢查询列表
    """
    # PostgreSQL查询慢查询日志
    bind_url = getattr(session.bind, "url", None)
    if bind_url and "postgresql" in str(bind_url):
        query = text("""
            SELECT
                query,
                calls,
                total_time,
                mean_time,
                max_time
            FROM pg_stat_statements
            WHERE mean_time > :threshold
            ORDER BY mean_time DESC
            LIMIT 20
        """)
        result = await session.execute(query, {"threshold": threshold_ms / 1000.0})
        rows = result.fetchall()

        return [
            {
                "sql": row[0],
                "calls": row[1],
                "total_time_ms": row[2] * 1000,
                "mean_time_ms": row[3] * 1000,
                "max_time_ms": row[4] * 1000,
            }
            for row in rows
        ]

    return []
