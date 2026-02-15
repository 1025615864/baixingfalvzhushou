"""周期任务服务

提供系统定时任务功能，包括订单超时处理、积分清理等。

功能特性:
    - 订单超时自动取消
    - 任务执行记录管理
    - 统计信息查询

使用示例:
    ```python
    from app.services.periodic_task_service import (
        PeriodicTaskService,
        OrderExpirationService,
    )

    # 检查超时订单
    result = await OrderExpirationService.check_and_cancel_expired_orders(db)
    ```
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from sqlalchemy.orm import selectinload

from ..models import PeriodicTaskRun, TaskStatus, PaymentOrder, PaymentStatus

logger = logging.getLogger("periodic_task")


class OrderExpirationService:
    """订单过期处理服务

    处理超时未支付的订单，自动取消并释放相关资源。

    功能:
        - 查询超时订单
        - 自动取消订单
        - 释放关联资源（配额、库存）
        - 记录处理日志
    """

    ORDER_TIMEOUT_HOURS = int(__import__("os").environ.get("ORDER_TIMEOUT_HOURS", "2"))
    BATCH_SIZE = 100

    @classmethod
    async def check_and_cancel_expired_orders(
        cls,
        db: AsyncSession,
        timeout_hours: int | None = None,
    ) -> dict:
        """检查并取消超时的待支付订单

        Args:
            db: 数据库会话
            timeout_hours: 超时时间（小时），默认使用配置值

        Returns:
            处理结果字典
        """
        timeout = timeout_hours or cls.ORDER_TIMEOUT_HOURS
        threshold = datetime.now(timezone.utc) - timedelta(hours=timeout)

        try:
            result = await db.execute(
                select(PaymentOrder)
                .where(PaymentOrder.status == PaymentStatus.PENDING)
                .where(PaymentOrder.expires_at < threshold)
                .limit(cls.BATCH_SIZE)
            )
            expired_orders = result.scalars().all()

            if not expired_orders:
                return {
                    "success": True,
                    "cancelled_count": 0,
                    "message": "没有超时的订单",
                }

            cancelled_ids = []
            released_resources = []

            for order in expired_orders:
                order.status = PaymentStatus.CANCELLED
                order.cancelled_at = datetime.now(timezone.utc)
                order.cancel_reason = "订单超时自动取消"
                cancelled_ids.append(order.id)

                resources = await cls._release_order_resources(db, order)
                if resources:
                    released_resources.extend(resources)

            await db.commit()

            logger.info(
                f"Cancelled {len(cancelled_ids)} expired orders, "
                f"released {len(released_resources)} resources"
            )

            return {
                "success": True,
                "cancelled_count": len(cancelled_ids),
                "order_ids": cancelled_ids[:10],
                "released_resources": len(released_resources),
                "message": f"已取消 {len(cancelled_ids)} 个超时订单",
            }

        except Exception as e:
            logger.exception(f"Failed to cancel expired orders: {e}")
            await db.rollback()
            return {
                "success": False,
                "cancelled_count": 0,
                "error": str(e),
                "message": "取消超时订单失败",
            }

    @classmethod
    async def _release_order_resources(
        cls,
        db: AsyncSession,
        order: PaymentOrder,
    ) -> list[str]:
        """释放订单关联的资源

        Args:
            db: 数据库会话
            order: 订单对象

        Returns:
            释放的资源列表
        """
        released = []

        try:
            if order.order_type == "ai_pack" and order.related_id:
                from ..models.user_quota import UserQuota
                from ..utils.deps import get_user_quota_service

                quota_service = get_user_quota_service()
                if quota_service:
                    quota = await quota_service.get_quota(db, order.user_id)
                    if quota:
                        restored = await quota_service.restore_quota(
                            db,
                            order.user_id,
                            order.related_id,
                        )
                        if restored:
                            released.append(
                                f"user_{order.user_id}_quota_{order.related_id}"
                            )

        except Exception as e:
            logger.warning(
                f"Failed to release resources for order {order.order_no}: {e}"
            )

        return released

    @classmethod
    async def get_expiration_stats(cls, db: AsyncSession) -> dict:
        """获取订单过期统计

        Returns:
            统计信息字典
        """
        now = datetime.now(timezone.utc)
        threshold_1h = now - timedelta(hours=1)
        threshold_2h = now - timedelta(hours=2)
        threshold_24h = now - timedelta(hours=24)

        stats = {
            "total_pending": 0,
            "expiring_soon_1h": 0,
            "expired_2h": 0,
            "expired_24h": 0,
        }

        result = await db.execute(select(PaymentOrder))
        orders = result.scalars().all()

        for order in orders:
            if order.status != PaymentStatus.PENDING:
                continue

            stats["total_pending"] += 1

            if order.expires_at < now:
                if order.expires_at > threshold_2h:
                    stats["expiring_soon_1h"] += 1
                elif order.expires_at > threshold_24h:
                    stats["expired_2h"] += 1
                else:
                    stats["expired_24h"] += 1

        return stats


class PeriodicTaskService:
    """周期任务服务类"""

    TASK_KEY_ORDER_EXPIRATION = "order_expiration"

    @staticmethod
    async def check_expired_orders(db: AsyncSession) -> dict:
        """检查并取消超时的待支付订单（兼容旧接口）

        Returns:
            dict: 处理结果，包含取消的订单数量
        """
        return await OrderExpirationService.check_and_cancel_expired_orders(db)

    @staticmethod
    async def create_run(
        db: AsyncSession,
        task_name: str,
        task_key: str,
    ) -> PeriodicTaskRun:
        """创建任务运行记录"""
        run = PeriodicTaskRun(
            task_name=task_name,
            task_key=task_key,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)
        return run

    @staticmethod
    async def complete_run(
        db: AsyncSession,
        run: PeriodicTaskRun,
        status: TaskStatus,
        result_summary: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> PeriodicTaskRun:
        """完成任务运行记录"""
        run.status = status
        run.completed_at = datetime.now(timezone.utc)
        started = run.started_at
        now = datetime.now(timezone.utc)
        if started is None:
            started = now
        else:
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
            delta = now - started
            run.duration_seconds = delta.total_seconds()
        if result_summary:
            run.result_summary = json.dumps(result_summary, ensure_ascii=False)
        if error_message:
            run.error_message = error_message
        await db.commit()
        await db.refresh(run)
        return run

    @staticmethod
    async def get_runs(
        db: AsyncSession,
        task_name: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PeriodicTaskRun]:
        """获取任务运行记录列表"""
        query = select(PeriodicTaskRun).order_by(
            desc(PeriodicTaskRun.created_at))
        if task_name:
            query = query.where(PeriodicTaskRun.task_name == task_name)
        if status:
            query = query.where(PeriodicTaskRun.status == status)
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_run_by_id(db: AsyncSession,
                            run_id: int) -> Optional[PeriodicTaskRun]:
        """根据ID获取任务运行记录"""
        result = await db.execute(
            select(PeriodicTaskRun).where(PeriodicTaskRun.id == run_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_latest_run(
        db: AsyncSession, task_key: str
    ) -> Optional[PeriodicTaskRun]:
        """获取任务最新运行记录"""
        result = await db.execute(
            select(PeriodicTaskRun)
            .where(PeriodicTaskRun.task_key == task_key)
            .order_by(desc(PeriodicTaskRun.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_task_stats(
        db: AsyncSession, task_key: str, hours: int = 24
    ) -> dict:
        """获取任务统计信息"""
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await db.execute(
            select(PeriodicTaskRun)
            .where(PeriodicTaskRun.task_key == task_key)
            .where(PeriodicTaskRun.created_at >= cutoff)
        )
        runs = list(result.scalars().all())

        total = len(runs)
        success = sum(1 for r in runs if r.status == TaskStatus.SUCCESS)
        failed = sum(1 for r in runs if r.status == TaskStatus.FAILED)
        avg_duration = (
            sum(r.duration_seconds or 0 for r in runs) /
            total if total > 0 else 0
        )

        return {
            "task_key": task_key,
            "period_hours": hours,
            "total_runs": total,
            "success_count": success,
            "failed_count": failed,
            "success_rate_percent": round(success / max(total, 1) * 100, 2),
            "avg_duration_seconds": round(avg_duration, 3),
        }


periodic_task_service = PeriodicTaskService()
