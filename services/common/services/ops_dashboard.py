"""统一运营看板基类

提供各服务管理后台通用的统计查询和审核日志方法。
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DashboardMixin:
    """运营看板通用方法混入类"""

    @staticmethod
    async def get_period_stats(
        session: AsyncSession,
        model_class,
        status_field: str = "status",
        status_values: Optional[List[str]] = None,
        date_field: str = "created_at",
        days: int = 30,
    ) -> Dict[str, Any]:
        """获取时间段内按状态分组的统计"""
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=days)

        date_col = getattr(model_class, date_field)
        conditions = [date_col >= period_start]

        if status_values:
            status_col = getattr(model_class, status_field)
            result = await session.execute(
                select(status_col, func.count())
                .where(*conditions)
                .group_by(status_col)
            )
            rows = result.all()
            return {row[0]: row[1] for row in rows}

        count_q = select(func.count()).select_from(model_class).where(*conditions)
        result = await session.execute(count_q)
        return {"total": result.scalar() or 0}

    @staticmethod
    async def get_today_count(
        session: AsyncSession,
        model_class,
        date_field: str = "created_at",
    ) -> int:
        """获取今日新增数量"""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        date_col = getattr(model_class, date_field)
        result = await session.execute(
            select(func.count()).select_from(model_class).where(date_col >= today_start)
        )
        return result.scalar() or 0

    @staticmethod
    async def get_week_count(
        session: AsyncSession,
        model_class,
        date_field: str = "created_at",
    ) -> int:
        """获取本周新增数量"""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        date_col = getattr(model_class, date_field)
        result = await session.execute(
            select(func.count()).select_from(model_class).where(date_col >= week_ago)
        )
        return result.scalar() or 0

    @staticmethod
    async def get_status_counts(
        session: AsyncSession,
        model_class,
        status_field: str = "status",
        statuses: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """按状态统计数量"""
        status_col = getattr(model_class, status_field)
        if statuses:
            result = await session.execute(
                select(status_col, func.count())
                .where(status_col.in_(statuses))
                .group_by(status_col)
            )
        else:
            result = await session.execute(
                select(status_col, func.count()).group_by(status_col)
            )

        rows = result.all()
        counts = {row[0]: row[1] for row in rows}
        if statuses:
            for s in statuses:
                counts.setdefault(s, 0)
        return counts

    @staticmethod
    async def get_trend_data(
        session: AsyncSession,
        model_class,
        date_field: str = "created_at",
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """获取最近 N 天的趋势数据"""
        now = datetime.now(timezone.utc)
        date_col = getattr(model_class, date_field)

        result = await session.execute(
            select(
                func.date_trunc("day", date_col).label("day"),
                func.count().label("count"),
            )
            .where(date_col >= now - timedelta(days=days))
            .group_by(func.date_trunc("day", date_col))
            .order_by(func.date_trunc("day", date_col))
        )

        return [
            {"date": row.day.isoformat() if row.day else None, "count": row.count}
            for row in result.all()
        ]


class AuditLogMixin:
    """审核日志通用方法混入类"""

    @staticmethod
    async def create_audit_log(
        session: AsyncSession,
        audit_model_class,
        target_id: int,
        operator_id: int,
        operator_name: Optional[str],
        action: str,
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
        comment: Optional[str] = None,
        extra_data: Optional[Dict] = None,
    ):
        """创建审核日志"""
        log = audit_model_class(
            **{
                _resolve_fk_field(audit_model_class): target_id,
                "operator_id": operator_id,
                "operator_name": operator_name,
                "action": action,
                "from_status": from_status,
                "to_status": to_status,
                "comment": comment,
                "extra_data": extra_data,
            }
        )
        session.add(log)
        await session.flush()
        return log

    @staticmethod
    async def get_audit_logs(
        session: AsyncSession,
        audit_model_class,
        target_id_field: str,
        target_id: Optional[int] = None,
        operator_id: Optional[int] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """查询审核日志"""
        conditions = []
        if target_id is not None:
            conditions.append(getattr(audit_model_class, target_id_field) == target_id)
        if operator_id is not None:
            conditions.append(audit_model_class.operator_id == operator_id)
        if action is not None:
            conditions.append(audit_model_class.action == action)

        base_query = select(audit_model_class).where(*conditions).order_by(audit_model_class.created_at.desc())
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        query = base_query.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(query)
        logs = result.scalars().all()

        return [
            {
                "id": log.id,
                target_id_field: getattr(log, target_id_field),
                "operator_id": log.operator_id,
                "operator_name": log.operator_name,
                "action": log.action,
                "from_status": log.from_status,
                "to_status": log.to_status,
                "comment": log.comment,
                "extra_data": log.extra_data,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ], total


def _resolve_fk_field(model_class) -> str:
    """自动推断审核日志模型的外键字段名"""
    for col_name in dir(model_class):
        if col_name.endswith("_id") and col_name not in ("id", "operator_id"):
            attr = getattr(model_class, col_name, None)
            if attr is not None and hasattr(attr, "property"):
                return col_name
    return "target_id"
