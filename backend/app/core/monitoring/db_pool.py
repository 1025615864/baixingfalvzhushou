"""数据库连接池监控"""
import logging
import time
import threading
from typing import Optional, Dict, Deque, Any
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class DBPoolMonitor:
    """数据库连接池监控器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.start_time = time.time()
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "slow_queries": 0,
            "total_query_time": 0.0,
        }
        self.query_history: Deque[Dict[str, Any]] = deque(maxlen=max_history)
        self.slow_query_threshold = 1.0  # 1秒
        self._lock = threading.Lock()
        
    def record_query(self, query_time: float, success: bool, query: Optional[str] = None):
        """记录查询信息"""
        with self._lock:
            self.stats["total_queries"] += 1
            self.stats["total_query_time"] += query_time
            
            if success:
                self.stats["successful_queries"] += 1
            else:
                self.stats["failed_queries"] += 1
                
            if query_time > self.slow_query_threshold:
                self.stats["slow_queries"] += 1
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "duration": query_time,
                    "success": success,
                    "query": query[:200] if query else None,  # 截断长查询
                }
                self.query_history.append(entry)
                query_preview = query[:100] if query else "N/A"
                logger.warning(f"慢查询检测: {query_time:.3f}s - {query_preview}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            avg_query_time = 0
            if self.stats["successful_queries"] > 0:
                avg_query_time = self.stats["total_query_time"] / self.stats["successful_queries"]
            
            uptime = time.time() - self.start_time
            qps = self.stats["total_queries"] / uptime if uptime > 0 else 0
            
            return {
                "uptime_seconds": uptime,
                "total_queries": self.stats["total_queries"],
                "successful_queries": self.stats["successful_queries"],
                "failed_queries": self.stats["failed_queries"],
                "slow_queries": self.stats["slow_queries"],
                "success_rate": (
                    self.stats["successful_queries"] / self.stats["total_queries"]
                    if self.stats["total_queries"] > 0 else 1.0
                ),
                "avg_query_time": avg_query_time,
                "queries_per_second": qps,
                "slow_query_threshold": self.slow_query_threshold,
                "slow_query_history_size": len(self.query_history),
            }
    
    def get_recent_slow_queries(self, limit: int = 10) -> list[Dict[str, Any]]:
        """获取最近的慢查询"""
        with self._lock:
            return list(self.query_history)[-limit:]
    
    def reset(self):
        """重置统计信息"""
        with self._lock:
            self.stats = {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "slow_queries": 0,
                "total_query_time": 0.0,
            }
            self.query_history.clear()
            self.start_time = time.time()


# 全局监控器实例
db_pool_monitor = DBPoolMonitor()
