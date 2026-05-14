"""Saga 和 Outbox 事务监控

提供分布式事务的执行监控、性能指标收集和告警。
支持：
- Saga 执行成功率、失败率、执行时间
- Outbox 消息堆积告警
- 失败事务告警
- Prometheus 指标暴露
"""
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from services.common.saga.orchestrator import SagaExecutionLog, SagaStatus, StepStatus
from services.common.outbox.publisher import OutboxMessage, OutboxStatus

logger = logging.getLogger(__name__)


class TransactionMonitor:
    """事务监控器"""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    def get_saga_stats(self, hours: int = 24) -> dict:
        """获取 Saga 执行统计"""
        db = self.db_session_factory()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            total = (
                db.query(SagaExecutionLog)
                .filter(SagaExecutionLog.created_at >= cutoff)
                .count()
            )

            completed = (
                db.query(SagaExecutionLog)
                .filter(
                    SagaExecutionLog.created_at >= cutoff,
                    SagaExecutionLog.status == SagaStatus.COMPLETED.value,
                )
                .count()
            )

            failed = (
                db.query(SagaExecutionLog)
                .filter(
                    SagaExecutionLog.created_at >= cutoff,
                    SagaExecutionLog.status == SagaStatus.FAILED.value,
                )
                .count()
            )

            compensating = (
                db.query(SagaExecutionLog)
                .filter(
                    SagaExecutionLog.created_at >= cutoff,
                    SagaExecutionLog.status.in_([
                        SagaStatus.COMPENSATING.value,
                        SagaStatus.COMPENSATED.value,
                    ]),
                )
                .count()
            )

            avg_duration = (
                db.query(func.avg(
                    func.extract("epoch", SagaExecutionLog.completed_at) -
                    func.extract("epoch", SagaExecutionLog.started_at)
                ))
                .filter(
                    SagaExecutionLog.created_at >= cutoff,
                    SagaExecutionLog.completed_at.isnot(None),
                )
                .scalar()
            )

            by_type = (
                db.query(
                    SagaExecutionLog.saga_type,
                    func.count(SagaExecutionLog.id),
                )
                .filter(SagaExecutionLog.created_at >= cutoff)
                .group_by(SagaExecutionLog.saga_type)
                .all()
            )

            return {
                "total": total,
                "completed": completed,
                "failed": failed,
                "compensating": compensating,
                "success_rate": completed / total if total > 0 else 0,
                "avg_duration_seconds": float(avg_duration) if avg_duration else 0,
                "by_type": {t: c for t, c in by_type},
            }
        finally:
            db.close()

    def get_outbox_stats(self) -> dict:
        """获取 Outbox 消息统计"""
        db = self.db_session_factory()

        try:
            pending = (
                db.query(OutboxMessage)
                .filter(OutboxMessage.status == OutboxStatus.PENDING.value)
                .count()
            )

            published = (
                db.query(OutboxMessage)
                .filter(OutboxMessage.status == OutboxStatus.PUBLISHED.value)
                .count()
            )

            failed = (
                db.query(OutboxMessage)
                .filter(OutboxMessage.status == OutboxStatus.FAILED.value)
                .count()
            )

            pending_oldest = (
                db.query(OutboxMessage.created_at)
                .filter(OutboxMessage.status == OutboxStatus.PENDING.value)
                .order_by(OutboxMessage.created_at.asc())
                .first()
            )

            pending_oldest_age = None
            if pending_oldest:
                pending_oldest_age = (datetime.now(timezone.utc) - pending_oldest[0]).total_seconds()

            return {
                "pending": pending,
                "published": published,
                "failed": failed,
                "pending_oldest_age_seconds": pending_oldest_age,
            }
        finally:
            db.close()

    def get_failed_sagas(self, hours: int = 24, limit: int = 50) -> list[dict]:
        """获取失败的 Saga 列表"""
        db = self.db_session_factory()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            failed = (
                db.query(SagaExecutionLog)
                .filter(
                    SagaExecutionLog.created_at >= cutoff,
                    SagaExecutionLog.status == SagaStatus.FAILED.value,
                )
                .order_by(desc(SagaExecutionLog.created_at))
                .limit(limit)
                .all()
            )

            return [
                {
                    "saga_id": s.id,
                    "saga_type": s.saga_type,
                    "status": s.status,
                    "error_message": s.error_message,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                    "steps": s.steps_log,
                }
                for s in failed
            ]
        finally:
            db.close()

    def get_stuck_sagas(self, timeout_minutes: int = 30) -> list[dict]:
        """获取卡住的 Saga（运行中但超时）"""
        db = self.db_session_factory()
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

        try:
            stuck = (
                db.query(SagaExecutionLog)
                .filter(
                    SagaExecutionLog.status == SagaStatus.RUNNING.value,
                    SagaExecutionLog.started_at < cutoff,
                )
                .order_by(desc(SagaExecutionLog.started_at))
                .all()
            )

            return [
                {
                    "saga_id": s.id,
                    "saga_type": s.saga_type,
                    "status": s.status,
                    "current_step": s.current_step,
                    "total_steps": s.total_steps,
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                    "stuck_minutes": (datetime.now(timezone.utc) - s.started_at).total_seconds() / 60,
                }
                for s in stuck
            ]
        finally:
            db.close()

    def get_prometheus_metrics(self) -> str:
        """生成 Prometheus 格式指标"""
        saga_stats = self.get_saga_stats()
        outbox_stats = self.get_outbox_stats()

        metrics = []

        metrics.append("# HELP saga_total Total number of saga executions")
        metrics.append("# TYPE saga_total counter")
        metrics.append(f"saga_total {saga_stats['total']}")

        metrics.append("# HELP saga_completed Number of completed saga executions")
        metrics.append("# TYPE saga_completed counter")
        metrics.append(f"saga_completed {saga_stats['completed']}")

        metrics.append("# HELP saga_failed Number of failed saga executions")
        metrics.append("# TYPE saga_failed counter")
        metrics.append(f"saga_failed {saga_stats['failed']}")

        metrics.append("# HELP saga_success_rate Saga success rate (0-1)")
        metrics.append("# TYPE saga_success_rate gauge")
        metrics.append(f"saga_success_rate {saga_stats['success_rate']:.4f}")

        metrics.append("# HELP saga_avg_duration_seconds Average saga execution duration in seconds")
        metrics.append("# TYPE saga_avg_duration_seconds gauge")
        metrics.append(f"saga_avg_duration_seconds {saga_stats['avg_duration_seconds']:.2f}")

        metrics.append("# HELP outbox_pending Number of pending outbox messages")
        metrics.append("# TYPE outbox_pending gauge")
        metrics.append(f"outbox_pending {outbox_stats['pending']}")

        metrics.append("# HELP outbox_failed Number of failed outbox messages")
        metrics.append("# TYPE outbox_failed gauge")
        metrics.append(f"outbox_failed {outbox_stats['failed']}")

        if outbox_stats.get("pending_oldest_age_seconds") is not None:
            metrics.append("# HELP outbox_oldest_pending_age_seconds Age of oldest pending outbox message")
            metrics.append("# TYPE outbox_oldest_pending_age_seconds gauge")
            metrics.append(f"outbox_oldest_pending_age_seconds {outbox_stats['pending_oldest_age_seconds']:.0f}")

        return "\n".join(metrics)

    def check_alerts(self) -> list[dict]:
        """检查告警条件"""
        alerts = []

        saga_stats = self.get_saga_stats()
        outbox_stats = self.get_outbox_stats()
        stuck_sagas = self.get_stuck_sagas()

        if saga_stats["total"] > 0 and saga_stats["success_rate"] < 0.95:
            alerts.append({
                "severity": "critical",
                "type": "saga_failure_rate",
                "message": f"Saga 失败率过高: {1 - saga_stats['success_rate']:.1%}",
                "details": saga_stats,
            })

        if outbox_stats["pending"] > 100:
            alerts.append({
                "severity": "warning",
                "type": "outbox_backlog",
                "message": f"Outbox 消息堆积: {outbox_stats['pending']} 条",
                "details": outbox_stats,
            })

        if outbox_stats["failed"] > 10:
            alerts.append({
                "severity": "critical",
                "type": "outbox_failures",
                "message": f"Outbox 消息失败过多: {outbox_stats['failed']} 条",
                "details": outbox_stats,
            })

        if outbox_stats.get("pending_oldest_age_seconds") and outbox_stats["pending_oldest_age_seconds"] > 3600:
            alerts.append({
                "severity": "warning",
                "type": "outbox_stale",
                "message": f"Outbox 消息停留过久: {outbox_stats['pending_oldest_age_seconds']:.0f} 秒",
                "details": outbox_stats,
            })

        if stuck_sagas:
            alerts.append({
                "severity": "critical",
                "type": "stuck_sagas",
                "message": f"发现 {len(stuck_sagas)} 个卡住的 Saga",
                "details": stuck_sagas,
            })

        return alerts
