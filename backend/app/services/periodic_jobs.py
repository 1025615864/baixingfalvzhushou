"""周期性任务定义

将 settlement、wechatpay certs refresh、review_sla 三个定时任务
从 main.py 迁移到此模块，减少 main.py 业务逻辑。
"""
from __future__ import annotations

import logging
import time
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.services.prometheus_metrics import prometheus_metrics

logger = logging.getLogger(__name__)


async def settlement_job_wrapper() -> object:
    """结算任务"""
    start = time.perf_counter()
    ok = True
    try:
        async with AsyncSessionLocal() as session:
            from app.services.settlement_service import settlement_service

            return await settlement_service.settle_due_income_records(session)
    except Exception:
        ok = False
        raise
    finally:
        prometheus_metrics.record_job(
            name="settlement",
            ok=bool(ok),
            duration_seconds=max(0.0, float(time.perf_counter() - start)),
        )


async def wechatpay_platform_certs_refresh_job_wrapper(settings) -> object:
    """微信支付平台证书刷新任务"""
    start = time.perf_counter()
    ok = True
    try:
        async with AsyncSessionLocal() as session:
            if not (
                settings.wechatpay_mch_id
                and settings.wechatpay_mch_serial_no
                and settings.wechatpay_private_key
                and settings.wechatpay_api_v3_key
            ):
                return {"skipped": True, "reason": "wechatpay config missing"}

            from app.models.system import SystemConfig
            from app.utils.payment.wechatpay_v3 import fetch_platform_certificates, dump_platform_certs_json

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
                    category="payment",
                    description="WeChatPay platform certificates cache",
                )
                session.add(row)
            else:
                row.value = raw
                row.category = "payment"
                if not (row.description or "").strip():
                    row.description = "WeChatPay platform certificates cache"
                session.add(row)

            await session.commit()
            return {"ok": True, "count": len(certs)}
    except Exception:
        ok = False
        raise
    finally:
        prometheus_metrics.record_job(
            name="wechatpay_platform_certs_refresh",
            ok=bool(ok),
            duration_seconds=max(0.0, float(time.perf_counter() - start)),
        )


async def review_task_sla_job_wrapper() -> object:
    """审核任务 SLA 扫描任务"""
    start = time.perf_counter()
    ok = True
    try:
        async with AsyncSessionLocal() as session:
            from app.services.review_task_sla_service import scan_and_notify_review_task_sla

            return await scan_and_notify_review_task_sla(session)
    except Exception:
        ok = False
        raise
    finally:
        prometheus_metrics.record_job(
            name="review_task_sla",
            ok=bool(ok),
            duration_seconds=max(0.0, float(time.perf_counter() - start)),
        )


class PeriodicJobsConfig:
    """周期性任务配置"""

    SETTLEMENT_INTERVAL_SECONDS = float(
        __import__("os").getenv("SETTLEMENT_JOB_INTERVAL_SECONDS", "3600").strip() or "3600"
    )
    WECHATPAY_CERT_REFRESH_INTERVAL_SECONDS = float(
        __import__("os").getenv("WECHATPAY_CERT_REFRESH_INTERVAL_SECONDS", "86400").strip() or "86400"
    )
    REVIEW_TASK_SLA_SCAN_INTERVAL_SECONDS = float(
        __import__("os").getenv("REVIEW_TASK_SLA_SCAN_INTERVAL_SECONDS", "60").strip() or "60"
    )

    @staticmethod
    def is_settlement_enabled(debug: bool, redis_connected: bool) -> bool:
        raw = __import__("os").getenv("SETTLEMENT_JOB_ENABLED", "").strip().lower()
        flag = raw in {"1", "true", "yes", "on"}
        enabled = bool(flag) or bool(debug)
        if (not debug) and (not redis_connected):
            enabled = False
        return enabled

    @staticmethod
    def is_wechatpay_refresh_enabled(debug: bool, redis_connected: bool) -> bool:
        raw = __import__("os").getenv("WECHATPAY_CERT_REFRESH_ENABLED", "").strip().lower()
        flag = raw in {"1", "true", "yes", "on"}
        enabled = bool(flag)
        if (not debug) and (not redis_connected):
            enabled = False
        return enabled

    @staticmethod
    def is_review_sla_enabled(debug: bool, redis_connected: bool) -> bool:
        raw = __import__("os").getenv("REVIEW_TASK_SLA_JOB_ENABLED", "").strip().lower()
        flag = raw in {"1", "true", "yes", "on"}
        enabled = bool(flag) or bool(debug)
        if (not debug) and (not redis_connected):
            enabled = False
        return enabled
