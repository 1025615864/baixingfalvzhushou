"""查询优化工具

提供 SQLAlchemy 预加载配置、查询性能分析和 N+1 查询检测功能。
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, Generic, List, Optional, Dict, Set
from functools import wraps

from sqlalchemy import select, Select
from sqlalchemy.orm import (
    selectinload,
    joinedload,
    Load,
    Query,
)
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.utils.logging.structured_logger import StructuredLogger

logger = StructuredLogger(__name__)

T = TypeVar("T")


@dataclass
class QueryPerformance:
    """查询性能指标"""
    query_name: str
    duration_ms: float
    query_count: int = 1
    n1_detected: bool = False
    optimization_applied: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class QueryStats:
    """查询统计信息"""
    total_queries: int = 0
    total_duration_ms: float = 0.0
    slow_queries: int = 0
    n1_queries_detected: int = 0
    optimizations_applied: int = 0
    
    @property
    def avg_duration_ms(self) -> float:
        """计算平均查询时间"""
        if self.total_queries == 0:
            return 0.0
        return self.total_duration_ms / self.total_queries
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_queries": self.total_queries,
            "total_duration_ms": round(self.total_duration_ms, 2),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "slow_queries": self.slow_queries,
            "n1_queries_detected": self.n1_queries_detected,
            "optimizations_applied": self.optimizations_applied,
        }


class QueryOptimizer:
    """查询优化器
    
    提供预加载配置、查询性能监控和 N+1 查询检测功能。
    """
    
    def __init__(
        self,
        slow_query_threshold_ms: float = 100.0,
        n1_detection_threshold: int = 5,
    ):
        """初始化查询优化器
        
        Args:
            slow_query_threshold_ms: 慢查询阈值（毫秒）
            n1_detection_threshold: N+1 查询检测阈值
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.n1_detection_threshold = n1_detection_threshold
        self.stats = QueryStats()
        self._query_history: List[QueryPerformance] = []
        self._n1_tracker: Dict[str, Set[int]] = {}
    
    def record_query(
        self,
        query_name: str,
        duration_ms: float,
        query_count: int = 1,
    ) -> QueryPerformance:
        """记录查询性能
        
        Args:
            query_name: 查询名称
            duration_ms: 查询耗时（毫秒）
            query_count: 查询次数
            
        Returns:
            查询性能指标
        """
        perf = QueryPerformance(
            query_name=query_name,
            duration_ms=duration_ms,
            query_count=query_count,
        )
        
        # 检测慢查询
        if duration_ms > self.slow_query_threshold_ms:
            perf.recommendations.append(
                f"慢查询：{duration_ms:.1f}ms > {self.slow_query_threshold_ms:.0f}ms"
            )
            self.stats.slow_queries += 1
        
        # 检测 N+1 查询
        if query_count > self.n1_detection_threshold:
            perf.n1_detected = True
            perf.recommendations.append(
                f"检测到 N+1 查询：{query_count} 次查询，建议预加载"
            )
            self.stats.n1_queries_detected += 1
        
        self._query_history.append(perf)
        self.stats.total_queries += 1
        self.stats.total_duration_ms += duration_ms
        
        return perf
    
    def apply_selectinload(
        self,
        query: Select,
        model: type,
        *relationships: str
    ) -> Select:
        """应用 selectinload 预加载
        
        适用于一对多关系，使用单独的 SELECT 语句加载关联对象。
        
        Args:
            query: 原始查询
            model: 模型类
            *relationships: 关系名称列表
            
        Returns:
            优化后的查询
        """
        for rel in relationships:
            try:
                query = query.options(selectinload(getattr(model, rel)))
                self.stats.optimizations_applied += 1
                logger.debug(f"应用 selectinload 预加载：{model.__name__}.{rel}")
            except AttributeError:
                logger.warning(f"关系不存在：{model.__name__}.{rel}")
        return query
    
    def apply_joinedload(
        self,
        query: Select,
        model: type,
        *relationships: str
    ) -> Select:
        """应用 joinedload 预加载
        
        适用于一对一关系，使用 JOIN 加载关联对象。
        
        Args:
            query: 原始查询
            model: 模型类
            *relationships: 关系名称列表
            
        Returns:
            优化后的查询
        """
        for rel in relationships:
            try:
                query = query.options(joinedload(getattr(model, rel)))
                self.stats.optimizations_applied += 1
                logger.debug(f"应用 joinedload 预加载：{model.__name__}.{rel}")
            except AttributeError:
                logger.warning(f"关系不存在：{model.__name__}.{rel}")
        return query
    
    def apply_preload(
        self,
        query: Select,
        model: type,
        relationships: List[tuple[str, str]]  # [(关系名，策略), ...]
    ) -> Select:
        """应用预加载配置
        
        Args:
            query: 原始查询
            model: 模型类
            relationships: 关系配置列表，每项为 (关系名，策略)
                          策略可选："selectinload" 或 "joinedload"
            
        Returns:
            优化后的查询
        """
        for rel_name, strategy in relationships:
            if strategy == "joinedload":
                query = self.apply_joinedload(query, model, rel_name)
            else:  # 默认 selectinload
                query = self.apply_selectinload(query, model, rel_name)
        return query
    
    def track_n1_query(self, operation_name: str, entity_id: int) -> bool:
        """跟踪 N+1 查询
        
        Args:
            operation_name: 操作名称
            entity_id: 实体 ID
            
        Returns:
            是否检测到 N+1 查询
        """
        if operation_name not in self._n1_tracker:
            self._n1_tracker[operation_name] = set()
        
        self._n1_tracker[operation_name].add(entity_id)
        count = len(self._n1_tracker[operation_name])
        
        return count > self.n1_detection_threshold
    
    def reset_n1_tracker(self, operation_name: Optional[str] = None) -> None:
        """重置 N+1 查询追踪器
        
        Args:
            operation_name: 操作名称，若为 None 则重置所有
        """
        if operation_name is None:
            self._n1_tracker.clear()
        elif operation_name in self._n1_tracker:
            self._n1_tracker[operation_name].clear()
    
    def get_stats(self) -> QueryStats:
        """获取查询统计"""
        return self.stats
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        recommendations = []
        for perf in self._query_history:
            if perf.recommendations:
                recommendations.append({
                    "query_name": perf.query_name,
                    "duration_ms": round(perf.duration_ms, 2),
                    "query_count": perf.query_count,
                    "n1_detected": perf.n1_detected,
                    "recommendations": perf.recommendations,
                })
        return recommendations
    
    def clear_history(self) -> None:
        """清除查询历史"""
        self._query_history.clear()
        self.stats = QueryStats()


# 全局查询优化器实例
query_optimizer = QueryOptimizer()


@contextmanager
def track_query(
    query_name: str,
    optimizer: Optional[QueryOptimizer] = None,
):
    """追踪查询性能的上下文管理器
    
    Args:
        query_name: 查询名称
        optimizer: 查询优化器实例，默认使用全局实例
    """
    opt = optimizer or query_optimizer
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        opt.record_query(query_name, duration_ms)


def monitor_queries(
    optimizer: Optional[QueryOptimizer] = None,
    slow_threshold_ms: float = 100.0,
):
    """查询性能监控装饰器
    
    Args:
        optimizer: 查询优化器实例
        slow_threshold_ms: 慢查询阈值
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            opt = optimizer or query_optimizer
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                opt.record_query(func.__name__, duration_ms)
                
                if duration_ms > slow_threshold_ms:
                    logger.warning(
                        f"慢查询检测：{func.__name__} 执行时间 {duration_ms:.1f}ms"
                    )
        return wrapper
    return decorator


# 预加载配置预设

class PreloadPresets:
    """预加载配置预设
    
    提供常用模型的预加载配置。
    """
    
    # 律师相关预加载配置
    LAWYER_BASIC = [
        ("firm", "joinedload"),  # 律师事务所（一对一）
    ]
    
    LAWYER_FULL = [
        ("firm", "joinedload"),
        ("user", "joinedload"),  # 关联用户（一对一）
    ]


def apply_lawyer_preload(
    query: Select,
    level: str = "basic"
) -> Select:
    """应用律师预加载配置
    
    Args:
        query: 原始查询
        level: 预加载级别 ("basic" 或 "full")
        
    Returns:
        优化后的查询
    """
    from app.models.lawfirm import Lawyer
    
    if level == "full":
        return query_optimizer.apply_preload(query, Lawyer, PreloadPresets.LAWYER_FULL)
    return query_optimizer.apply_preload(query, Lawyer, PreloadPresets.LAWYER_BASIC)


# N+1 查询检测工具

class N1QueryDetector:
    """N+1 查询检测器
    
    用于检测循环中的重复查询模式。
    """
    
    def __init__(self, threshold: int = 5):
        """初始化检测器
        
        Args:
            threshold: 检测阈值（超过此次数视为 N+1 查询）
        """
        self.threshold = threshold
        self._access_counts: Dict[str, int] = {}
        self._detected: List[Dict[str, Any]] = []
    
    def track_access(self, relationship: str, entity_id: int) -> None:
        """追踪关系访问
        
        Args:
            relationship: 关系名称
            entity_id: 实体 ID
        """
        key = f"{relationship}:{entity_id}"
        self._access_counts[key] = self._access_counts.get(key, 0) + 1
    
    def detect_n1(self, relationship: str) -> bool:
        """检测是否存在 N+1 查询
        
        Args:
            relationship: 关系名称
            
        Returns:
            是否检测到 N+1 查询
        """
        count = sum(
            v for k, v in self._access_counts.items()
            if k.startswith(f"{relationship}:")
        )
        return count > self.threshold
    
    def get_report(self) -> Dict[str, Any]:
        """获取检测报告"""
        n1_relationships = []
        for rel in set(k.split(":")[0] for k in self._access_counts.keys()):
            if self.detect_n1(rel):
                n1_relationships.append(rel)
        
        return {
            "threshold": self.threshold,
            "total_accesses": sum(self._access_counts.values()),
            "n1_detected": len(n1_relationships),
            "n1_relationships": n1_relationships,
            "access_counts": dict(self._access_counts),
        }
    
    def reset(self) -> None:
        """重置检测器"""
        self._access_counts.clear()
        self._detected.clear()


def get_query_optimizer() -> QueryOptimizer:
    """获取全局查询优化器实例"""
    return query_optimizer


def get_query_stats() -> Dict[str, Any]:
    """获取查询统计信息"""
    return query_optimizer.get_stats().to_dict()


def get_query_recommendations() -> List[Dict[str, Any]]:
    """获取查询优化建议"""
    return query_optimizer.get_recommendations()