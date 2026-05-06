"""案例统计分析服务"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.archive import Base

logger = logging.getLogger(__name__)


class CaseStatisticsService:
    """案例统计分析服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_court_level(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """按法院级别统计"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        query = self.db.execute(
            f"""
            SELECT court_level, COUNT(*) as count
            FROM legal_case
            WHERE is_deleted = false
            AND created_at >= :start_date
            AND created_at <= :end_date
            GROUP BY court_level
            ORDER BY count DESC
            """,
            {"start_date": start_date, "end_date": end_date}
        ).fetchall()

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "distribution": [
                {"court_level": row[0] or "unknown", "count": row[1]}
                for row in query
            ]
        }

    def get_by_case_type(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """按案件类型统计"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        query = self.db.execute(
            f"""
            SELECT case_type, COUNT(*) as count
            FROM legal_case
            WHERE is_deleted = false
            AND created_at >= :start_date
            AND created_at <= :end_date
            GROUP BY case_type
            ORDER BY count DESC
            """,
            {"start_date": start_date, "end_date": end_date}
        ).fetchall()

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "distribution": [
                {"case_type": row[0] or "unknown", "count": row[1]}
                for row in query
            ]
        }

    def get_by_cause(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 20) -> Dict:
        """按案由统计"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        query = self.db.execute(
            f"""
            SELECT cause_of_action, COUNT(*) as count
            FROM legal_case
            WHERE is_deleted = false
            AND cause_of_action IS NOT NULL
            AND created_at >= :start_date
            AND created_at <= :end_date
            GROUP BY cause_of_action
            ORDER BY count DESC
            LIMIT :limit
            """,
            {"start_date": start_date, "end_date": end_date, "limit": limit}
        ).fetchall()

        total = sum(row[1] for row in query)

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "top_causes": [
                {
                    "cause_of_action": row[0],
                    "count": row[1],
                    "percentage": round(row[1] / total * 100, 2) if total > 0 else 0
                }
                for row in query
            ]
        }

    def get_trends(self, group_by: str = "month", start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """获取趋势统计"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()

        if group_by == "month":
            date_format = "%Y-%m"
        elif group_by == "week":
            date_format = "%Y-W%V"
        else:
            date_format = "%Y-%m-%d"

        query = self.db.execute(
            f"""
            SELECT
                DATE_FORMAT(created_at, '{date_format}') as period,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published,
                SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END) as archived
            FROM legal_case
            WHERE is_deleted = false
            AND created_at >= :start_date
            AND created_at <= :end_date
            GROUP BY period
            ORDER BY period
            """,
            {"start_date": start_date, "end_date": end_date}
        ).fetchall()

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "group_by": group_by,
            "trends": [
                {
                    "period": row[0],
                    "total": row[1],
                    "published": row[2],
                    "archived": row[3]
                }
                for row in query
            ]
        }

    def get_summary(self) -> Dict:
        """获取统计摘要"""
        total_query = self.db.execute(
            "SELECT COUNT(*) FROM legal_case WHERE is_deleted = false"
        ).fetchone()

        published_query = self.db.execute(
            "SELECT COUNT(*) FROM legal_case WHERE is_deleted = false AND status = 'published'"
        ).fetchone()

        guiding_query = self.db.execute(
            "SELECT COUNT(*) FROM legal_case WHERE is_deleted = false AND is_guiding_case = true"
        ).fetchone()

        return {
            "total_cases": total_query[0] if total_query else 0,
            "published_cases": published_query[0] if published_query else 0,
            "guiding_cases": guiding_query[0] if guiding_query else 0,
            "retrieved_at": datetime.now().isoformat()
        }
