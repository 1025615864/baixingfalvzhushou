"""审计日志服务"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.models.ops_models import OpsAuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        operator_id: int,
        action: str,
        target_type: str,
        target_id: int = None,
        detail: str = None,
        operator_role: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> OpsAuditLog:
        log = OpsAuditLog(
            operator_id=operator_id,
            operator_role=operator_role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def query_logs(
        self,
        operator_id: int = None,
        action: str = None,
        target_type: str = None,
        target_id: int = None,
        period_days: int = 7,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[OpsAuditLog], int]:
        conditions = []

        if operator_id:
            conditions.append(OpsAuditLog.operator_id == operator_id)
        if action:
            conditions.append(OpsAuditLog.action == action)
        if target_type:
            conditions.append(OpsAuditLog.target_type == target_type)
        if target_id:
            conditions.append(OpsAuditLog.target_id == target_id)

        period_cutoff = datetime.now() - timedelta(days=period_days)
        conditions.append(OpsAuditLog.created_at >= period_cutoff)

        query = select(OpsAuditLog).where(and_(*conditions))
        query = query.order_by(OpsAuditLog.created_at.desc())

        count_result = await self.db.execute(
            select(func.count()).select_from(OpsAuditLog).where(and_(*conditions))
        )
        total = count_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)

        return list(result.scalars().all()), total

    async def get_log_by_id(self, log_id: int) -> Optional[OpsAuditLog]:
        result = await self.db.execute(
            select(OpsAuditLog).where(OpsAuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def get_audit_summary(
        self,
        operator_id: int = None,
        period_days: int = 7
    ) -> dict:
        period_cutoff = datetime.now() - timedelta(days=period_days)

        conditions = [OpsAuditLog.created_at >= period_cutoff]
        if operator_id:
            conditions.append(OpsAuditLog.operator_id == operator_id)

        result = await self.db.execute(
            select(
                OpsAuditLog.action,
                func.count(OpsAuditLog.id).label("count")
            )
            .where(and_(*conditions))
            .group_by(OpsAuditLog.action)
        )

        action_counts = {row.action: row.count for row in result.all()}

        return {
            "period_days": period_days,
            "total_actions": sum(action_counts.values()),
            "by_action": action_counts
        }
