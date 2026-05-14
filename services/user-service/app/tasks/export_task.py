"""异步数据导出任务处理器"""
import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import ExportTask, ExportStatus
from ..models import User, UserProfile, LoginAudit, AuditLog
from ..services.data_export_service import DataExportService

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
TASK_EXPIRY_HOURS = 24


class ExportTaskProcessor:
    """异步导出任务处理器"""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """启动导出任务处理器"""
        if self._running:
            logger.warning("Export task processor already running")
            return

        self._running = True
        self._shutdown_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Export task processor started")

    async def stop(self):
        """停止导出任务处理器"""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Export task processor shutdown timeout")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        logger.info("Export task processor stopped")

    async def _run_loop(self):
        """运行处理循环"""
        while not self._shutdown_event.is_set():
            try:
                await self._process_pending_tasks()
                await self._cleanup_expired_tasks()
            except Exception as e:
                logger.error(f"Export task processing error: {e}")

            await asyncio.wait_for(
                self._shutdown_event.wait(),
                timeout=5.0
            )

    async def _process_pending_tasks(self):
        """处理待处理的导出任务"""
        async with AsyncSessionLocal() as session:
            stmt = (
                select(ExportTask)
                .where(ExportTask.status == ExportStatus.PENDING)
                .order_by(ExportTask.created_at)
                .limit(10)
                .with_for_update(skip_locked=True)
            )
            result = await session.execute(stmt)
            tasks = list(result.scalars().all())

            for export_task in tasks:
                await self._process_task(session, export_task)

            await session.commit()

    async def _process_task(self, session: AsyncSession, export_task: ExportTask):
        """处理单个导出任务"""
        try:
            export_task.status = ExportStatus.PROCESSING
            export_task.started_at = datetime.now(timezone.utc)
            export_task.progress = 10
            await session.commit()

            data_export_service = DataExportService(session)
            export_task.progress = 30

            user_data = await data_export_service.export_user_data(export_task.user_id)
            export_task.progress = 70

            if export_task.format == "json":
                result_data = user_data
            elif export_task.format == "csv":
                result_data = self._convert_to_csv(user_data)
            else:
                result_data = user_data

            export_task.progress = 90
            export_task.result_data = result_data
            export_task.status = ExportStatus.COMPLETED
            export_task.completed_at = datetime.now(timezone.utc)
            export_task.expires_at = datetime.now(timezone.utc) + timedelta(hours=TASK_EXPIRY_HOURS)

            logger.info(f"Export task completed: task_id={export_task.id}, user_id={export_task.user_id}")

        except Exception as e:
            export_task.status = ExportStatus.FAILED
            export_task.error_message = str(e)[:500]
            export_task.completed_at = datetime.now(timezone.utc)
            logger.error(f"Export task failed: task_id={export_task.id}, error={e}")

    async def _cleanup_expired_tasks(self):
        """清理过期的导出任务"""
        async with AsyncSessionLocal() as session:
            now = datetime.now(timezone.utc)
            stmt = (
                update(ExportTask)
                .where(ExportTask.expires_at <= now)
                .where(ExportTask.status == ExportStatus.COMPLETED)
                .values(status=ExportStatus.EXPIRED)
            )
            await session.execute(stmt)
            await session.commit()

    def _convert_to_csv(self, data: dict) -> dict:
        """将数据转换为CSV格式（返回扁平化结构供前端转换）"""
        basic_info = data.get("basic_info", {})
        account_info = data.get("account_info", {})

        csv_fields = {
            "exported_at": data.get("export_info", {}).get("exported_at", ""),
            "user_id": basic_info.get("id", ""),
            "username": basic_info.get("username", ""),
            "email": basic_info.get("email", ""),
            "phone": basic_info.get("phone", ""),
            "role": basic_info.get("role", ""),
            "status": basic_info.get("status", ""),
            "vip_expires_at": account_info.get("vip_expires_at", ""),
            "email_verified": account_info.get("email_verified", ""),
            "phone_verified": account_info.get("phone_verified", ""),
            "account_created_at": basic_info.get("created_at", ""),
        }

        return {
            "csv_data": csv_fields,
            "json_data": data,
            "format": "csv"
        }

    async def create_export_task(
        self,
        session: AsyncSession,
        user_id: int,
        format: str = "json"
    ) -> ExportTask:
        """创建导出任务"""
        task = ExportTask(
            id=str(uuid.uuid4()),
            user_id=user_id,
            format=format,
            status=ExportStatus.PENDING,
            progress=0,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        logger.info(f"Export task created: task_id={task.id}, user_id={user_id}")
        return task

    async def get_task_status(
        self,
        session: AsyncSession,
        task_id: str,
        user_id: int
    ) -> Optional[ExportTask]:
        """获取任务状态"""
        stmt = select(ExportTask).where(
            ExportTask.id == task_id,
            ExportTask.user_id == user_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


import uuid
export_task_processor = ExportTaskProcessor()
