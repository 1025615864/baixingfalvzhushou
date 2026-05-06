"""检索日志服务"""
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from collections import Counter

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.retrieval_log import RetrievalLog

logger = logging.getLogger(__name__)


class RetrievalLogService:
    """检索日志服务"""

    def __init__(self, db: Session):
        self.db = db

    def log_retrieval(
        self,
        conversation_id: str,
        query: str,
        intent: str,
        retrieval_level: str,
        docs_retrieved: int,
        docs_used: int,
        latency_ms: int,
        cache_hit: bool = False,
        sources: Optional[Dict] = None
    ) -> RetrievalLog:
        """记录检索日志"""
        log = RetrievalLog(
            conversation_id=conversation_id,
            query=query,
            intent=intent,
            retrieval_level=retrieval_level,
            docs_retrieved=docs_retrieved,
            docs_used=docs_used,
            latency_ms=latency_ms,
            cache_hit=cache_hit,
            sources=sources or {}
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_hit_rate_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day"
    ) -> Dict:
        """获取命中率统计"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()

        date_format = "%Y-%m-%d"
        if group_by == "hour":
            date_format = "%Y-%m-%d %H:00"

        query = self.db.query(
            func.date_format(RetrievalLog.created_at, date_format).label("period"),
            func.count(RetrievalLog.id).label("total"),
            func.sum(func.cast(RetrievalLog.cache_hit, Integer)).label("cache_hits")
        ).filter(
            and_(
                RetrievalLog.created_at >= start_date,
                RetrievalLog.created_at <= end_date
            )
        ).group_by("period").all()

        stats = []
        for row in query:
            total = row.total or 0
            cache_hits = row.cache_hits or 0
            hit_rate = (cache_hits / total * 100) if total > 0 else 0
            stats.append({
                "period": row.period,
                "total": total,
                "cache_hits": cache_hits,
                "hit_rate": round(hit_rate, 2)
            })

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "group_by": group_by,
            "stats": stats
        }

    def get_level_distribution(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """获取各层级使用分布"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()

        query = self.db.query(
            RetrievalLog.retrieval_level,
            func.count(RetrievalLog.id).label("count")
        ).filter(
            and_(
                RetrievalLog.created_at >= start_date,
                RetrievalLog.created_at <= end_date
            )
        ).group_by(RetrievalLog.retrieval_level).all()

        total = sum(row.count for row in query)
        distribution = []
        for row in query:
            percentage = (row.count / total * 100) if total > 0 else 0
            distribution.append({
                "level": row.retrieval_level,
                "count": row.count,
                "percentage": round(percentage, 2)
            })

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total": total,
            "distribution": distribution
        }

    def get_unmatched_queries(
        self,
        min_count: int = 3,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """获取未命中查询聚合（检索结果为0或使用fallback的查询）"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()

        query = self.db.query(
            RetrievalLog.query,
            func.count(RetrievalLog.id).label("count"),
            func.max(RetrievalLog.retrieval_level).label("worst_level"),
            func.avg(RetrievalLog.docs_retrieved).label("avg_docs")
        ).filter(
            and_(
                RetrievalLog.created_at >= start_date,
                RetrievalLog.created_at <= end_date,
                RetrievalLog.retrieval_level.in_(["level_2_backend", "level_3_fallback"])
            )
        ).group_by(
            RetrievalLog.query
        ).having(
            func.count(RetrievalLog.id) >= min_count
        ).order_by(
            func.count(RetrievalLog.id).desc()
        ).limit(100).all()

        return [
            {
                "query": row.query,
                "count": row.count,
                "worst_level": row.worst_level,
                "avg_docs_retrieved": round(row.avg_docs or 0, 2)
            }
            for row in query
        ]

    def get_latency_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """获取延迟统计"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()

        query = self.db.query(
            RetrievalLog.retrieval_level,
            func.avg(RetrievalLog.latency_ms).label("avg_latency"),
            func.min(RetrievalLog.latency_ms).label("min_latency"),
            func.max(RetrievalLog.latency_ms).label("max_latency"),
            func.percentile_cont(0.5).within_group(RetrievalLog.latency_ms).label("p50_latency"),
            func.percentile_cont(0.95).within_group(RetrievalLog.latency_ms).label("p95_latency")
        ).filter(
            and_(
                RetrievalLog.created_at >= start_date,
                RetrievalLog.created_at <= end_date
            )
        ).group_by(RetrievalLog.retrieval_level).all()

        stats = []
        for row in query:
            stats.append({
                "level": row.retrieval_level,
                "avg_latency_ms": round(row.avg_latency or 0, 2),
                "min_latency_ms": row.min_latency or 0,
                "max_latency_ms": row.max_latency or 0,
                "p50_latency_ms": round(row.p50_latency or 0, 2),
                "p95_latency_ms": round(row.p95_latency or 0, 2)
            })

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "stats": stats
        }


from sqlalchemy import Integer
