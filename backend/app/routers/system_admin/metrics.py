"""系统监控指标路由"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Query, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.prometheus_metrics import prometheus_metrics
from ...services.system_monitor import get_system_monitor
from sqlalchemy import select, desc

router = APIRouter(prefix="/metrics", tags=["系统监控"])


@router.get("", summary="获取 Prometheus 格式的监控指标")
async def get_prometheus_metrics(
    _current_user: Annotated[None, None] = None,  # 公开端点，无需认证
):
    """
    获取 Prometheus 格式的监控指标

    包含：
    - HTTP 请求计数和延迟分布
    - 周期任务执行状态
    - 支付指标
    - SQL 慢查询指标
    """
    metrics_text = prometheus_metrics.render_prometheus()
    return PlainTextResponse(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/summary", summary="获取监控指标摘要")
async def get_metrics_summary(
    hours: int = Query(1, ge=1, le=24, description="回看小时数"),
):
    """
    获取关键监控指标的摘要

    返回：
    - API 成功率、延迟（P50/P95）
    - AI 响应时间
    - 支付成功率
    - 系统健康状态
    """
    # 获取 HTTP 指标快照
    http_snap = prometheus_metrics.snapshot_http()

    # 计算关键指标
    total_requests = 0
    error_requests = 0
    total_duration = 0.0
    durations = []

    for key, agg in http_snap.items():
        count = int(agg.count)
        total_requests += count
        total_duration += float(agg.sum_seconds)

        if key.status.startswith("5"):
            error_requests += count

        # 收集延迟数据用于计算百分位
        if agg.bucket_le_counts:
            for le, c in agg.bucket_le_counts.items():
                for _ in range(int(c)):
                    durations.append(float(le))

    # 计算成功率
    success_rate = (total_requests - error_requests) / \
        max(total_requests, 1) * 100

    # 计算 P50/P95 延迟
    durations.sort()
    p50 = durations[len(durations) // 2] if durations else 0
    p95 = durations[int(len(durations) * 0.95)] if durations else 0

    # 获取任务状态
    jobs_snap = prometheus_metrics.snapshot_jobs()
    job_status = []
    for name, agg in jobs_snap.items():
        if int(agg.runs_total) > 0:
            job_status.append({
                "name": name,
                "success_rate": int(agg.successes_total) / max(int(agg.runs_total), 1) * 100,
                "last_run": datetime.fromtimestamp(agg.last_run_ts).isoformat() if agg.last_run_ts else None,
                "last_duration_seconds": agg.last_duration_seconds,
            })

    # 获取系统监控数据
    monitor = get_system_monitor()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period_hours": hours,
        "api": {
            "total_requests": total_requests,
            "success_rate_percent": round(
                success_rate,
                2),
            "error_5xx_count": error_requests,
            "latency_p50_seconds": round(
                p50,
                4),
            "latency_p95_seconds": round(
                p95,
                4),
            "avg_duration_seconds": round(
                total_duration / max(
                    total_requests,
                    1),
                4) if total_requests > 0 else 0,
        },
        "jobs": job_status,
        "health": monitor.get_health_status(),
    }


@router.get("/health", summary="获取系统健康状态")
async def get_health_check():
    """获取系统健康状态"""
    monitor = get_system_monitor()
    return monitor.get_health_status()


@router.get("/alerts", summary="获取活跃告警")
async def get_alerts(
    _current_user: Annotated[None, None] = None,
    hours: int = Query(24, ge=1, le=168, description="回看小时数"),
):
    """获取活跃告警列表"""
    monitor = get_system_monitor()
    alerts = monitor.get_recent_alerts(hours=hours)
    return {
        "alerts": [
            {
                "rule_name": a.rule_name,
                "level": a.level.value,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
                "resolved": a.resolved,
            }
            for a in alerts
        ],
        "total": len(alerts),
    }


@router.get("/alerts/rules", summary="获取告警规则列表")
async def get_alert_rules(
    _current_user: Annotated[None, None] = None,
):
    """获取所有告警规则及其状态"""
    monitor = get_system_monitor()
    return {
        "rules": [
            {
                "name": rule.name,
                "description": rule.description,
                "level": rule.level.value,
                "cooldown_seconds": rule.cooldown_seconds,
                "enabled": rule.enabled,
            }
            for rule in monitor._alert_rules
        ],
        "total": len(monitor._alert_rules),
    }


@router.get("/alerts/history", summary="获取告警历史")
async def get_alert_history(
    _current_user: Annotated[None, None] = None,
    hours: int = Query(24, ge=1, le=168, description="回看小时数"),
    level: str | None = Query(None, description="过滤告警级别"),
    resolved: bool | None = Query(None, description="过滤是否已解决"),
):
    """获取告警历史记录"""
    monitor = get_system_monitor()
    alerts = monitor.get_recent_alerts(hours=hours)

    if level:
        alerts = [a for a in alerts if a.level.value == level]
    if resolved is not None:
        alerts = [a for a in alerts if a.resolved == resolved]

    return {
        "alerts": [
            {
                "rule_name": a.rule_name,
                "level": a.level.value,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
                "resolved": a.resolved,
            }
            for a in alerts
        ],
        "total": len(alerts),
    }


@router.post("/alerts/check", summary="手动触发告警检查")
async def check_alerts(
    _current_user: Annotated[None, None] = None,
):
    """手动触发告警检查并返回当前告警状态"""
    monitor = get_system_monitor()
    new_alerts = monitor.check_alerts()
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "new_alerts_count": len(new_alerts),
        "alerts": [
            {
                "rule_name": a.rule_name,
                "level": a.level.value,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
            }
            for a in new_alerts
        ],
    }


@router.get("/periodic-tasks", summary="获取周期任务状态")
async def get_periodic_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    task_name: str | None = None,
    limit: int = Query(50, ge=1, le=100),
):
    """
    获取周期任务运行状态（从数据库读取）

    返回：
    - 任务运行历史记录
    - 任务统计信息
    - 任务状态分布
    """
    from ...services.periodic_task_service import periodic_task_service
    from ...models import TaskStatus

    # 获取任务运行记录
    runs = await periodic_task_service.get_runs(db, task_name=task_name, limit=limit)

    # 构建响应
    run_list = []
    for run in runs:
        run_list.append({
            "id": run.id,
            "task_name": run.task_name,
            "task_key": run.task_key,
            "status": run.status.value if hasattr(run.status, 'value') else str(run.status),
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "duration_seconds": run.duration_seconds,
            "error_message": run.error_message,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        })

    # 计算统计信息
    status_counts = {s.value: 0 for s in TaskStatus}
    for run in runs:
        status = run.status.value if hasattr(
            run.status, 'value') else str(
            run.status)
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "runs": run_list,
        "total": len(run_list),
        "status_counts": status_counts,
    }


@router.get("/periodic-tasks/stats", summary="获取周期任务统计")
async def get_periodic_task_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    task_key: str,
    hours: int = Query(24, ge=1, le=168),
):
    """
    获取指定任务的统计信息

    返回：
    - 总运行次数
    - 成功/失败次数
    - 成功率
    - 平均执行时长
    """
    from ...services.periodic_task_service import periodic_task_service

    stats = await periodic_task_service.get_task_stats(db, task_key, hours)
    return stats


@router.get("/periodic-tasks/overview", summary="获取周期任务概览")
async def get_periodic_tasks_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    hours: int = Query(24, ge=1, le=168),
):
    """
    获取所有周期任务的概览统计

    返回：
    - 各任务运行次数、成功率、平均时长
    - 整体健康状态
    - 最近失败记录
    """
    from ...services.periodic_task_service import periodic_task_service
    from ...models import TaskStatus, PeriodicTaskRun
    from sqlalchemy import select, func

    task_keys = [
        "locks:scheduled_news",
        "locks:rss_ingest",
        "locks:news_ai_pipeline",
        "locks:settlement",
        "locks:wechatpay_platform_certs",
        "locks:review_task_sla",
    ]

    overview = []
    recent_failures = []

    for task_key in task_keys:
        stats = await periodic_task_service.get_task_stats(db, task_key, hours)
        overview.append({
            "task_key": task_key,
            "task_name": task_key.replace("locks:", "").replace("_", " ").title(),
            "total_runs": stats.get("total_runs", 0),
            "success_count": stats.get("success_count", 0),
            "failed_count": stats.get("failed_count", 0),
            "success_rate_percent": stats.get("success_rate_percent", 0),
            "avg_duration_seconds": stats.get("avg_duration_seconds", 0),
        })

    # 获取最近失败记录
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(PeriodicTaskRun)
        .where(PeriodicTaskRun.status == TaskStatus.FAILED)
        .where(PeriodicTaskRun.created_at >= cutoff)
        .order_by(desc(PeriodicTaskRun.created_at))
        .limit(10)
    )
    failures = result.scalars().all()
    for f in failures:
        recent_failures.append({
            "id": f.id,
            "task_name": f.task_name,
            "task_key": f.task_key,
            "error_message": f.error_message,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "duration_seconds": f.duration_seconds,
        })

    total_runs = sum(o["total_runs"] for o in overview)
    total_failures = sum(o["failed_count"] for o in overview)
    overall_success_rate = (
        (total_runs - total_failures) / max(total_runs, 1)) * 100

    return {
        "period_hours": hours,
        "overview": overview,
        "summary": {
            "total_runs": total_runs,
            "total_failures": total_failures,
            "overall_success_rate_percent": round(overall_success_rate, 2),
            "task_count": len(overview),
        },
        "recent_failures": recent_failures,
        "recent_failures_count": len(recent_failures),
    }
