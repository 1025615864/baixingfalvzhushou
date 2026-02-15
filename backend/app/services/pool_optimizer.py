"""连接池优化工具

优化数据库连接池配置。
"""
from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


class ConnectionPoolOptimizer:
    """连接池优化器"""

    def __init__(
        self,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
    ) -> None:
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle

    def get_optimized_pool_config(self) -> dict[str, Any]:
        """获取优化的连接池配置

        Returns:
            连接池配置
        """
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,  # 连接前ping检查
            "echo": False,  # 不输出SQL日志
        }

    async def analyze_pool_usage(
        self,
        session: AsyncSession
    ) -> dict[str, Any]:
        """分析连接池使用情况

        Args:
            session: 数据库会话

        Returns:
            连接池使用统计
        """
        # PostgreSQL查询连接池状态
        if "postgresql" in str(session.bind.url):
            query = text("""
                SELECT
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
            """)
            result = await session.execute(query)
            row = result.fetchone()

            return {
                "total_connections": row[0],
                "active_connections": row[1],
                "idle_connections": row[2],
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
                "utilization": row[0] / (self.pool_size + self.max_overflow),
            }

        return {}

    async def get_optimization_suggestions(
        self,
        usage_stats: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """获取优化建议

        Args:
            usage_stats: 使用统计

        Returns:
            优化建议列表
        """
        suggestions = []

        # 检查连接池利用率
        utilization = usage_stats.get("utilization", 0)
        if utilization > 0.9:
            suggestions.append({
                "issue": "连接池利用率过高",
                "current_utilization": f"{utilization:.2%}",
                "target_utilization": "<80%",
                "suggestion": "增加连接池大小（pool_size）",
            })
        elif utilization < 0.3:
            suggestions.append({
                "issue": "连接池利用率过低",
                "current_utilization": f"{utilization:.2%}",
                "target_utilization": "50-80%",
                "suggestion": "减少连接池大小以节省资源",
            })

        # 检查活跃连接数
        active = usage_stats.get("active_connections", 0)
        total = usage_stats.get("total_connections", 0)
        if active > total * 0.8:
            suggestions.append({
                "issue": "活跃连接数过多",
                "active_connections": active,
                "total_connections": total,
                "suggestion": "检查是否有连接泄漏",
            })

        return suggestions


# 全局连接池优化器
pool_optimizer = ConnectionPoolOptimizer()


def get_pool_config_suggestions(
    pool_size: int = 20,
    max_overflow: int = 10,
    pool_timeout: int = 30,
    pool_recycle: int = 3600
) -> dict[str, Any]:
    """获取连接池配置建议

    Args:
        pool_size: 连接池大小
        max_overflow: 最大溢出
        pool_timeout: 超时时间
        pool_recycle: 回收时间

    Returns:
        配置建议
    """
    suggestions = []

    # 连接池大小建议
    if pool_size < 10:
        suggestions.append({
            "parameter": "pool_size",
            "current_value": pool_size,
            "suggested_value": 20,
            "reason": "连接池大小过小，可能导致连接等待",
        })
    elif pool_size > 50:
        suggestions.append({
            "parameter": "pool_size",
            "current_value": pool_size,
            "suggested_value": 30,
            "reason": "连接池大小过大，浪费资源",
        })

    # 最大溢出建议
    if max_overflow < 5:
        suggestions.append({
            "parameter": "max_overflow",
            "current_value": max_overflow,
            "suggested_value": 10,
            "reason": "溢出大小过小，无法应对突发流量",
        })

    # 超时时间建议
    if pool_timeout < 10:
        suggestions.append({
            "parameter": "pool_timeout",
            "current_value": pool_timeout,
            "suggested_value": 30,
            "reason": "超时时间过短，可能导致频繁超时",
        })

    # 回收时间建议
    if pool_recycle < 1800:
        suggestions.append({
            "parameter": "pool_recycle",
            "current_value": pool_recycle,
            "suggested_value": 3600,
            "reason": "回收时间过短，可能导致频繁回收",
        })

    return {
        "current_config": {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_recycle": pool_recycle,
        },
        "suggestions": suggestions,
    }


# 连接池优化最佳实践
POOL_OPTIMIZATION_BEST_PRACTICES = {
    "pool_size": {
        "description": "连接池大小",
        "recommendation": "20-30",
        "reason": "平衡性能和资源使用",
    },
    "max_overflow": {
        "description": "最大溢出",
        "recommendation": "10-20",
        "reason": "应对突发流量",
    },
    "pool_timeout": {
        "description": "连接超时",
        "recommendation": "30秒",
        "reason": "避免长时间等待",
    },
    "pool_recycle": {
        "description": "连接回收",
        "recommendation": "3600秒",
        "reason": "定期回收连接，避免连接问题",
    },
    "pool_pre_ping": {
        "description": "连接前ping",
        "recommendation": "True",
        "reason": "检查连接是否有效",
    },
}
