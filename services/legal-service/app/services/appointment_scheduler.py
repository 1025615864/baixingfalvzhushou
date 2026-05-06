"""预约定时任务调度器"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SchedulerMetrics:
    """调度器指标"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_expired_appointments: int = 0
    total_no_shows: int = 0
    last_execution_time: Optional[datetime] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None


class AppointmentScheduler:
    """预约超时定时任务调度器"""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self._running = False
        self._task = None
        self._metrics = SchedulerMetrics()

    @property
    def metrics(self) -> SchedulerMetrics:
        """获取当前指标"""
        return self._metrics

    def get_stats(self) -> dict:
        """获取调度器统计信息"""
        return {
            "running": self._running,
            "total_executions": self._metrics.total_executions,
            "successful_executions": self._metrics.successful_executions,
            "failed_executions": self._metrics.failed_executions,
            "total_expired_appointments": self._metrics.total_expired_appointments,
            "total_no_shows": self._metrics.total_no_shows,
            "last_execution_time": self._metrics.last_execution_time.isoformat() if self._metrics.last_execution_time else None,
            "last_error": self._metrics.last_error,
            "last_error_time": self._metrics.last_error_time.isoformat() if self._metrics.last_error_time else None,
        }

    async def start(self, interval_seconds: int = 60):
        """启动定时调度器"""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop(interval_seconds))
        logger.info(
            "appointment_scheduler_started",
            extra={"interval_seconds": interval_seconds}
        )

    async def stop(self):
        """停止定时调度器"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(
            "appointment_scheduler_stopped",
            extra={"total_executions": self._metrics.total_executions}
        )

    async def _run_loop(self, interval_seconds: int):
        """定时任务循环"""
        while self._running:
            try:
                await asyncio.sleep(interval_seconds)
                await self._process_timeouts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "appointment_scheduler_loop_error",
                    extra={"error": str(e)}
                )

    async def _process_timeouts(self):
        """处理超时预约"""
        self._metrics.total_executions += 1
        execution_start = datetime.utcnow()

        try:
            async with self.db_session_factory() as db:
                from app.services.appointment_service import AppointmentService
                service = AppointmentService(db)

                timeout_result = await service.handle_timeout_appointments()
                expired_count = timeout_result.get("expired_count", 0)
                released_slots = timeout_result.get("released_slots", 0)

                if expired_count > 0:
                    logger.info(
                        "appointment_expired_processed",
                        extra={
                            "expired_count": expired_count,
                            "released_slots": released_slots,
                        }
                    )

                no_show_result = await service.handle_scheduled_time_past()
                no_show_count = no_show_result.get("no_show_count", 0)

                if no_show_count > 0:
                    logger.info(
                        "appointment_no_show_processed",
                        extra={"no_show_count": no_show_count}
                    )

                self._metrics.successful_executions += 1
                self._metrics.total_expired_appointments += expired_count
                self._metrics.total_no_shows += no_show_count
                self._metrics.last_execution_time = datetime.utcnow()

        except Exception as e:
            self._metrics.failed_executions += 1
            self._metrics.last_error = str(e)
            self._metrics.last_error_time = datetime.utcnow()
            logger.error(
                "appointment_scheduler_process_error",
                extra={
                    "error": str(e),
                    "execution_start": execution_start.isoformat(),
                }
            )

    async def run_once(self):
        """手动执行一次（用于测试）"""
        await self._process_timeouts()


_scheduler: AppointmentScheduler = None


def get_scheduler(db_session_factory) -> AppointmentScheduler:
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AppointmentScheduler(db_session_factory)
    return _scheduler
