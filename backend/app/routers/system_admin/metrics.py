"""System admin metrics endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.services.prometheus_metrics import PrometheusMetrics
from app.services.system_monitor import get_system_monitor

router = APIRouter(prefix="/metrics", tags=["metrics"])

prometheus_metrics = PrometheusMetrics()


async def get_prometheus_metrics() -> PlainTextResponse:
    content = prometheus_metrics.render_prometheus()
    return PlainTextResponse(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")


@router.get("/summary")
async def get_metrics_summary(hours: int = 1):
    monitor = get_system_monitor()
    http_snap = prometheus_metrics.snapshot_http()
    jobs_snap = prometheus_metrics.snapshot_jobs()
    total_requests = sum(agg.count for agg in http_snap.values()) if http_snap else 0
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period_hours": hours,
        "api": {
            "total_requests": total_requests,
            "http": {str(k): {"count": v.count, "sum_seconds": v.sum_seconds} for k, v in http_snap.items()} if http_snap else {},
        },
        "jobs": {str(k): {"count": v.count} for k, v in jobs_snap.items()} if jobs_snap else {},
        "health": monitor.get_health_status(),
    }


@router.get("/health")
async def get_health_check():
    monitor = get_system_monitor()
    return monitor.get_health_status()


@router.get("/alerts")
async def get_alerts(hours: int = 24):
    monitor = get_system_monitor()
    alerts = monitor.get_recent_alerts(hours=hours)
    return {
        "alerts": [
            {
                "rule_name": a.rule_name,
                "level": a.level.value,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
            }
            for a in alerts
        ],
        "total": len(alerts),
    }
