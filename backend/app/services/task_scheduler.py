"""定时任务配置模块

提供统一的定时任务配置和任务包装器，减少main.py中的重复代码。
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
import typing
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.services.cache_service import cache_service
from app.services.periodic_task_service import periodic_task_service
from app.services.prometheus_metrics import prometheus_metrics
from app.utils.periodic_task_runner import PeriodicLockedRunner
from app.models import TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class TaskConfig:
    """任务配置"""
    name: str  # 任务名称
    lock_key: str  # Redis锁键
    lock_ttl_seconds: int = 60  # 锁过期时间
    interval_seconds: float = 60.0  # 执行间隔
    enabled_env_var: str | None = None  # 环境变量名称（如果需要动态启用）
    enabled_default: bool = True  # 默认启用状态


@dataclass
class TaskResult:
    """任务执行结果"""
    success: bool
    result: dict | None = None
    error_message: str | None = None
    duration_seconds: float = 0.0


class TaskWrapper:
    """任务包装器

    提供统一的任务执行逻辑，包括：
    - 数据库会话管理
    - 任务运行记录
    - 异常处理
    - 指标记录
    """

    def __init__(
        self,
        name: str,
        job_func: Callable[[AsyncSession], Awaitable[typing.Any]],
    ):
        self.name = name
        self.job_func = job_func

    async def run(self) -> TaskResult:
        """执行任务"""
        start_time = time.perf_counter()
        ok = True
        run = None
        result_value = None
        error_message: str | None = None

        try:
            async with AsyncSessionLocal() as session:
                run = await periodic_task_service.create_run(
                    session,
                    task_name=self.name,
                    task_key=f"locks:{self.name}"
                )

                result_value = await self.job_func(session)

                result_summary = (
                    result_value
                    if isinstance(result_value, dict)
                    else {"result": str(result_value)}
                )
                await periodic_task_service.complete_run(
                    session, run, TaskStatus.SUCCESS, result_summary
                )

        except Exception as e:
            ok = False
            error_message = str(e)
            logger.exception(f"Task {self.name} failed: {e}")

            if run:
                try:
                    async with AsyncSessionLocal() as session:
                        await periodic_task_service.complete_run(
                            session,
                            run,
                            TaskStatus.FAILED,
                            error_message=error_message
                        )
                except (ConnectionError, TimeoutError) as conn_err:
                    logger.error(f"Database connection error while recording task failure: {conn_err}")
                except Exception as cleanup_err:
                    logger.warning(f"Failed to record task failure status: {cleanup_err}")

        finally:
            duration = max(0.0, float(time.perf_counter() - start_time))
            prometheus_metrics.record_job(
                name=self.name,
                ok=bool(ok),
                duration_seconds=duration,
            )

        return TaskResult(
            success=ok,
            result={"value": str(result_value)} if result_value else None,
            error_message=error_message,
            duration_seconds=duration,
        )


class TaskScheduler:
    """任务调度器

    管理应用的所有定时任务，提供统一的启动和停止接口。
    """

    def __init__(self, runner: PeriodicLockedRunner):
        self.runner = runner
        self.tasks: list[asyncio.Task[None] | None] = []
        self.task_wrappers: dict[str, TaskWrapper] = {}

    def add_task(
        self,
        config: TaskConfig,
        job_func: Callable[[AsyncSession], Awaitable[typing.Any]],
    ) -> None:
        """添加任务"""
        wrapper = TaskWrapper(config.name, job_func)
        self.task_wrappers[config.name] = wrapper

        async def wrapper_func() -> typing.Any:
            result = await wrapper.run()
            return result

        task = asyncio.create_task(
            self.runner.run(
                lock_key=config.lock_key,
                lock_ttl_seconds=config.lock_ttl_seconds,
                interval_seconds=config.interval_seconds,
                job=wrapper_func,
            )
        )
        self.tasks.append(task)
        logger.info(f"Task '{config.name}' scheduled (interval={config.interval_seconds}s)")

    async def start_all(
        self,
        redis_connected: bool,
        debug: bool,
        settings: typing.Any,
    ) -> list[asyncio.Task[None] | None]:
        """启动所有任务

        Args:
            redis_connected: Redis连接状态
            debug: 调试模式
            settings: 应用配置

        Returns:
            任务列表（可能包含None）
        """
        from app.services.news_service import news_service
        from app.services.rss_ingest_service import rss_ingest_service
        from app.services.news_ai_pipeline_service import news_ai_pipeline_service
        from app.services.settlement_service import settlement_service
        from app.services.review_task_sla_service import scan_and_notify_review_task_sla
        from app.utils.wechatpay_v3 import (
            fetch_platform_certificates,
            dump_platform_certs_json,
        )
        from app.models import SystemConfig
        from sqlalchemy import select

        # RSS订阅任务 (已迁移到news-service)
        rss_feeds_raw = os.getenv("RSS_FEEDS", "").strip()
        rss_ingest_enabled_raw = os.getenv("RSS_INGEST_ENABLED", "").strip().lower()
        rss_enabled = bool(rss_feeds_raw) or bool(rss_ingest_enabled_raw in {"1", "true", "yes", "on"}) or debug
        if rss_enabled and (debug or redis_connected):
            rss_interval = float(os.getenv("RSS_INGEST_INTERVAL_SECONDS", "300").strip() or "300")
            self.add_task(
                TaskConfig(
                    name="rss_ingest",
                    lock_key="locks:rss_ingest",
                    interval_seconds=rss_interval,
                ),
                lambda session: rss_ingest_service.run_once(session),
            )

        # 结算任务
        settlement_enabled_raw = os.getenv("SETTLEMENT_JOB_ENABLED", "").strip().lower()
        settlement_enabled = settlement_enabled_raw in {"1", "true", "yes", "on"} or debug
        if settlement_enabled and (debug or redis_connected):
            settlement_interval = float(os.getenv("SETTLEMENT_JOB_INTERVAL_SECONDS", "3600").strip() or "3600")
            self.add_task(
                TaskConfig(
                    name="settlement",
                    lock_key="locks:settlement",
                    interval_seconds=settlement_interval,
                ),
                lambda session: settlement_service.settle_due_income_records(session),
            )

        # 微信支付证书刷新任务
        wechatpay_refresh_enabled_raw = os.getenv("WECHATPAY_CERT_REFRESH_ENABLED", "").strip().lower()
        wechatpay_refresh_enabled = wechatpay_refresh_enabled_raw in {"1", "true", "yes", "on"}
        if wechatpay_refresh_enabled and (debug or redis_connected):
            wechatpay_interval = float(os.getenv("WECHATPAY_CERT_REFRESH_INTERVAL_SECONDS", "86400").strip() or "86400")

            async def refresh_wechatpay_certs(session: AsyncSession) -> dict:
                if not (settings.wechatpay_mch_id and settings.wechatpay_mch_serial_no and
                        settings.wechatpay_private_key and settings.wechatpay_api_v3_key):
                    return {"skipped": True, "reason": "wechatpay config missing"}

                certs = await fetch_platform_certificates(
                    certificates_url=settings.wechatpay_certificates_url,
                    mch_id=settings.wechatpay_mch_id,
                    mch_serial_no=settings.wechatpay_mch_serial_no,
                    mch_private_key_pem=settings.wechatpay_private_key,
                    api_v3_key=settings.wechatpay_api_v3_key,
                )
                raw = dump_platform_certs_json(certs)

                res = await session.execute(
                    select(SystemConfig).where(SystemConfig.key == "WECHATPAY_PLATFORM_CERTS_JSON")
                )
                row = res.scalar_one_or_none()
                if row is None:
                    row = SystemConfig(
                        key="WECHATPAY_PLATFORM_CERTS_JSON",
                        value=raw,
                        description="微信支付平台证书JSON",
                    )
                    session.add(row)
                else:
                    row.value = raw
                await session.commit()
                return {"updated": True}

            self.add_task(
                TaskConfig(
                    name="wechatpay_cert_refresh",
                    lock_key="locks:wechatpay_cert_refresh",
                    lock_ttl_seconds=120,
                    interval_seconds=wechatpay_interval,
                ),
                refresh_wechatpay_certs,
            )

        # 审核任务SLA任务
        review_sla_enabled_raw = os.getenv("REVIEW_TASK_SLA_JOB_ENABLED", "").strip().lower()
        review_sla_enabled = review_sla_enabled_raw in {"1", "true", "yes", "on"} or debug
        if review_sla_enabled and (debug or redis_connected):
            review_sla_interval = float(os.getenv("REVIEW_TASK_SLA_SCAN_INTERVAL_SECONDS", "60").strip() or "60")
            self.add_task(
                TaskConfig(
                    name="review_task_sla",
                    lock_key="locks:review_task_sla",
                    interval_seconds=review_sla_interval,
                ),
                lambda session: scan_and_notify_review_task_sla(session),
            )

        # 订单超时检查任务
        self.add_task(
            TaskConfig(
                name="order_timeout_check",
                lock_key="locks:order_timeout_check",
                interval_seconds=300.0,
            ),
            lambda session: periodic_task_service.check_expired_orders(session),
        )

        logger.info(f"Total tasks scheduled: {len(self.tasks)}")
        return self.tasks

    async def stop_all(self) -> None:
        """停止所有任务"""
        cancelled_count = 0
        for task in self.tasks:
            if task is None:
                continue
            task.cancel()
            try:
                await task
                cancelled_count += 1
            except asyncio.CancelledError:
                cancelled_count += 1
                pass
            except asyncio.TimeoutError as timeout_err:
                logger.warning(f"Task cancellation timeout: {timeout_err}")
            except Exception as stop_err:
                logger.debug(f"Task cancellation error: {stop_err}")
        logger.info(f"Stopped {cancelled_count}/{len(self.tasks)} tasks")


def get_task_scheduler(runner: PeriodicLockedRunner) -> TaskScheduler:
    """获取任务调度器实例"""
    return TaskScheduler(runner)


async def cleanup_token_blacklist(session: AsyncSession) -> dict[str, int]:
    """清理过期的Token黑名单记录
    
    Returns:
        清理的记录数量
    """
    from app.core.token_rotation import TokenRotation, TOKEN_BLACKLIST_PREFIX
    
    redis = TokenRotation._get_redis()
    if not redis or not redis.is_connected:
        return {"skipped": True, "reason": "redis not connected"}
    
    try:
        pattern = f"{TOKEN_BLACKLIST_PREFIX}:*"
        cursor = 0
        cleaned = 0
        
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            for key in keys:
                ttl = await redis.ttl(key)
                if ttl <= 0:
                    await redis.delete(key)
                    cleaned += 1
            
            if cursor == 0:
                break
        
        logger.info(f"Cleaned {cleaned} expired token blacklist entries")
        return {"cleaned": cleaned}
    except Exception as e:
        logger.error(f"Failed to cleanup token blacklist: {e}")
        return {"error": str(e)}
