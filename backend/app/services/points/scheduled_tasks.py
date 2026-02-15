"""积分系统定时任务

提供每日任务重置、统计汇总等功能。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import AsyncSessionLocal, engine
from ...models import (
    PointsUser,
    PointsDailyCount,
    PointsHistory,
    PointsExchangeOrder,
)
from .points_service_db import PointsServiceDB

logger = logging.getLogger(__name__)


class PointsScheduledTasks:
    """积分系统定时任务"""

    def __init__(self):
        self._daily_reset_task: Optional[asyncio.Task] = None
        self._stats_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def reset_daily_counts(self, date: Optional[str] = None) -> int:
        """重置每日计数

        Args:
            date: 日期，默认为今天 (YYYY-MM-DD)

        Returns:
            清理的记录数
        """
        date = date or datetime.now().strftime("%Y-%m-%d")

        async with AsyncSessionLocal() as db:
            # 将前一天的数据归档到历史
            yesterday = (datetime.strptime(date, "%Y-%m-%d") -
                         timedelta(days=1)).strftime("%Y-%m-%d")

            # 统计昨日数据
            result = await db.execute(
                select(
                    PointsDailyCount.user_id,
                    PointsDailyCount.action,
                    func.sum(PointsDailyCount.count).label("total_count"),
                )
                .where(PointsDailyCount.date == yesterday)
                .group_by(PointsDailyCount.user_id, PointsDailyCount.action)
            )
            daily_stats = result.all()

            # 归档到历史表（这里简单记录到 points_history）
            for user_id, action, total_count in daily_stats:
                if total_count > 0:
                    history = PointsHistory(
                        user_id=user_id,
                        action=f"daily_stat_{action}",
                        points=0,
                        balance_before=0,
                        balance_after=0,
                        description=f"{date} {action} 完成 {total_count} 次",
                        extra_data={
                            "date": yesterday,
                            "action": action,
                            "count": total_count},
                    )
                    db.add(history)

            # 删除旧数据（保留7天）
            old_date = (datetime.strptime(date, "%Y-%m-%d") -
                        timedelta(days=7)).strftime("%Y-%m-%d")
            from sqlalchemy import delete
            await db.execute(
                delete(PointsDailyCount).where(
                    PointsDailyCount.date < old_date)
            )

            # 重置今日之前的记录
            await db.execute(
                delete(PointsDailyCount).where(PointsDailyCount.date == date)
            )

            await db.commit()

            count = len(daily_stats)
            logger.info(f"每日积分计数已重置，清理了 {count} 条记录 ({date})")
            return count

    async def generate_daily_report(self, date: Optional[str] = None) -> dict:
        """生成每日统计报告

        Args:
            date: 日期，默认为昨天

        Returns:
            统计报告字典
        """
        date = date or (
            datetime.now() -
            timedelta(
                days=1)).strftime("%Y-%m-%d")

        async with AsyncSessionLocal() as db:
            # 用户增长
            result = await db.execute(
                select(func.count(PointsUser.id)).where(
                    PointsUser.created_at >= f"{date} 00:00:00",
                    PointsUser.created_at < f"{date} 23:59:59",
                )
            )
            new_users = result.scalar() or 0

            # 积分发放统计
            result = await db.execute(
                select(
                    PointsHistory.action,
                    func.sum(PointsHistory.points).label("total_points"),
                    func.count(PointsHistory.id).label("total_count"),
                )
                .where(
                    PointsHistory.created_at >= f"{date} 00:00:00",
                    PointsHistory.created_at < f"{date} 23:59:59",
                    PointsHistory.points > 0,
                )
                .group_by(PointsHistory.action)
            )
            issued_stats = {
                row.action: {
                    "points": row.total_points,
                    "count": row.total_count} for row in result.all()}

            # 积分消耗统计
            result = await db.execute(
                select(
                    func.sum(-PointsHistory.points).label("total_spent"),
                    func.count(PointsHistory.id).label("total_count"),
                )
                .where(
                    PointsHistory.created_at >= f"{date} 00:00:00",
                    PointsHistory.created_at < f"{date} 23:59:59",
                    PointsHistory.points < 0,
                )
            )
            spent_row = result.one()
            total_spent = spent_row.total_spent or 0
            spent_count = spent_row.total_count or 0

            # 签到统计
            result = await db.execute(
                select(func.count(PointsUser.id)).where(
                    PointsUser.last_signin_at >= f"{date} 00:00:00",
                    PointsUser.last_signin_at < f"{date} 23:59:59",
                )
            )
            signin_count = result.scalar() or 0

            # 连续签到达人
            result = await db.execute(
                select(PointsUser).order_by(
                    PointsUser.continuous_signin_days.desc()).limit(10)
            )
            top_signers = [
                {"user_id": u.user_id, "continuous_days": u.continuous_signin_days}
                for u in result.scalars().all()
            ]

            report = {
                "date": date,
                "new_users": new_users,
                "signin_count": signin_count,
                "points_issued": issued_stats,
                "points_spent": {"total": total_spent, "count": spent_count},
                "top_signers": top_signers,
                "generated_at": datetime.now().isoformat(),
            }

            logger.info(f"每日积分报告已生成: {date}")
            return report

    async def cleanup_expired_orders(self, days: int = 30) -> int:
        """清理过期的兑换订单

        Args:
            days: 订单保留天数，默认30天

        Returns:
            清理的订单数
        """
        from sqlalchemy import delete

        async with AsyncSessionLocal() as db:
            cutoff = (
                datetime.now() -
                timedelta(
                    days=days)).strftime("%Y-%m-%d")

            stmt = delete(PointsExchangeOrder).where(
                PointsExchangeOrder.status == "pending",
                PointsExchangeOrder.created_at < f"{cutoff} 00:00:00",
            )
            result = await db.execute(stmt)

            count = result.rowcount  # type: ignore[assignment]
            await db.commit()

            if count > 0:
                logger.info(f"已清理 {count} 个过期兑换订单")

            return count

    async def run_daily_tasks(self):
        """执行每日任务（凌晨执行）"""
        if self._is_running:
            logger.warning("每日任务已在运行中，跳过")
            return

        self._is_running = True
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            logger.info("开始执行积分系统每日任务...")

            # 1. 重置每日计数
            await self.reset_daily_counts(today)

            # 2. 生成昨日报告
            await self.generate_daily_report()

            # 3. 清理过期订单
            await self.cleanup_expired_orders()

            logger.info("积分系统每日任务执行完成")

        except Exception as e:
            logger.error(f"积分系统每日任务执行失败: {e}")

        finally:
            self._is_running = False

    def start_scheduler(self, check_interval: int = 60):
        """启动调度器（后台任务）

        Args:
            check_interval: 检查间隔（秒），默认60秒
        """
        async def scheduler_loop():
            while True:
                try:
                    now = datetime.now()

                    # 每天凌晨 2 点执行任务
                    if now.hour == 2 and now.minute == 0:
                        await self.run_daily_tasks()

                    # 检查是否需要执行
                    next_hour = now.hour + 1 if now.minute < 60 else now.hour
                    await asyncio.sleep(60)

                except Exception as e:
                    logger.error(f"调度器错误: {e}")
                    await asyncio.sleep(60)

        self._daily_reset_task = asyncio.create_task(scheduler_loop())
        logger.info("积分系统调度器已启动")

    def stop_scheduler(self):
        """停止调度器"""
        if self._daily_reset_task:
            self._daily_reset_task.cancel()
            self._daily_reset_task = None
            logger.info("积分系统调度器已停止")


# 单例
_points_scheduled_tasks: Optional[PointsScheduledTasks] = None


def get_points_scheduled_tasks() -> PointsScheduledTasks:
    """获取定时任务单例"""
    global _points_scheduled_tasks
    if _points_scheduled_tasks is None:
        _points_scheduled_tasks = PointsScheduledTasks()
    return _points_scheduled_tasks
