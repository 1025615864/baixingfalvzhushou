"""管理员监控路由

提供系统监控和性能管理API。
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..core.monitoring.query_monitor import get_query_stats, reset_query_stats  # type: ignore[import-untyped]
from ..services.slow_query_analyzer import slow_query_analyzer  # type: ignore[import-untyped]
from ..services.system_monitor import get_system_monitor, get_health_check, AlertLevel
from ..services.enhanced_websocket import enhanced_manager
from ..config import get_settings
from ..database import get_db
from ..models.user import User
from ..utils.deps import get_current_user

try:
    import redis.asyncio as redis  # type: ignore[import-not-found]
    _has_redis = True
except ImportError:
    _has_redis = False  # type: ignore[misc]

try:
    import psutil  # type: ignore[import-not-found]
    _has_psutil = True
except ImportError:
    _has_psutil = False  # type: ignore[misc]

try:
    import platform
    _has_platform = True
except ImportError:
    _has_platform = False  # type: ignore[misc]

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/monitor", tags=["admin-monitor"])


@router.get("/query-stats", summary="获取查询统计")
async def get_query_statistics() -> dict[str, Any]:
    """获取SQL查询统计信息
    
    包括总查询数、慢查询数、平均执行时间等。
    """
    stats = get_query_stats()
    suggestions = slow_query_analyzer.get_optimization_suggestions()
    
    return {
        "stats": stats,
        "slow_queries": slow_query_analyzer.get_slow_queries(limit=20),
        "optimization_suggestions": suggestions,
    }


@router.post("/query-stats/reset", summary="重置查询统计")
async def reset_query_statistics() -> dict[str, str]:
    """重置SQL查询统计信息"""
    reset_query_stats()
    slow_query_analyzer.slow_queries.clear()
    slow_query_analyzer.query_stats.clear()
    
    return {"message": "查询统计已重置"}


@router.get("/slow-queries", summary="获取慢查询列表")
async def get_slow_queries_list(limit: int = 20) -> dict[str, Any]:
    """获取慢查询列表
    
    Args:
        limit: 返回数量限制
    """
    return {
        "slow_queries": slow_query_analyzer.get_slow_queries(limit=limit),
        "count": len(slow_query_analyzer.slow_queries),
        "stats": slow_query_analyzer.get_query_stats(),
    }


@router.get("/optimization-suggestions", summary="获取优化建议")
async def get_optimization_suggestions() -> dict[str, Any]:
    """获取查询优化建议"""
    suggestions = slow_query_analyzer.get_optimization_suggestions()
    
    return {
        "suggestions_count": len(suggestions),
        "suggestions": suggestions,
    }


# 健康检查
async def get_health() -> dict[str, Any]:
    """获取系统健康状态"""
    return get_health_check()


@router.get("/health", summary="健康检查")
async def get_health_endpoint() -> dict[str, Any]:
    """获取系统健康状态"""
    return await get_health()


# 指标相关
async def get_metrics(hours: int = 1) -> dict[str, Any]:
    """获取监控指标汇总"""
    monitor = get_system_monitor()
    return monitor.get_metrics_summary()


@router.get("/metrics", summary="获取监控指标")
async def get_metrics_endpoint(hours: int = 1) -> dict[str, Any]:
    """获取监控指标汇总"""
    return await get_metrics(hours=hours)


async def get_api_metrics(endpoint: Optional[str] = None, hours: int = 1) -> dict[str, Any]:
    """获取API性能指标"""
    monitor = get_system_monitor()
    
    if endpoint:
        stats = monitor.get_timer_stats(f"api.{endpoint}")
        return {
            "endpoint": endpoint,
            "stats": stats,
        }
    else:
        # 返回所有端点的指标
        endpoints = {}
        for key in monitor._timers.keys():
            if key.startswith("api."):
                ep_name = key[4:]  # 移除 "api." 前缀
                endpoints[ep_name] = monitor.get_timer_stats(key)
        return {
            "endpoints": endpoints,
            "count": len(endpoints),
        }


@router.get("/api-metrics", summary="获取API性能指标")
async def get_api_metrics_endpoint(
    endpoint: Optional[str] = None,
    hours: int = 1
) -> dict[str, Any]:
    """获取API性能指标"""
    return await get_api_metrics(endpoint=endpoint, hours=hours)


async def get_ai_metrics(hours: int = 1) -> dict[str, Any]:
    """获取AI服务指标"""
    monitor = get_system_monitor()
    return {
        "response_time": monitor.get_timer_stats("ai.response"),
        "total_responses": monitor.get_counter("ai.response.total"),
        "total_tokens": monitor.get_counter("ai.response.tokens"),
    }


@router.get("/ai-metrics", summary="获取AI服务指标")
async def get_ai_metrics_endpoint(hours: int = 1) -> dict[str, Any]:
    """获取AI服务指标"""
    return await get_ai_metrics(hours=hours)


async def get_user_metrics() -> dict[str, Any]:
    """获取用户活跃指标"""
    monitor = get_system_monitor()
    return {
        "active_now": monitor.get_counter("user.active"),
        "registered_total": monitor.get_counter("user.registered"),
        "vip_users": monitor.get_counter("user.vip"),
    }


@router.get("/user-metrics", summary="获取用户活跃指标")
async def get_user_metrics_endpoint() -> dict[str, Any]:
    """获取用户活跃指标"""
    return await get_user_metrics()


async def get_business_metrics() -> dict[str, Any]:
    """获取业务指标"""
    monitor = get_system_monitor()
    return {
        "consultations": monitor.get_counter("business.consultation"),
        "documents_generated": monitor.get_counter("business.document"),
        "lawyer_bookings": monitor.get_counter("business.booking"),
        "posts_created": monitor.get_counter("business.post"),
    }


@router.get("/business-metrics", summary="获取业务指标")
async def get_business_metrics_endpoint() -> dict[str, Any]:
    """获取业务指标"""
    return await get_business_metrics()


# 告警相关
async def get_alerts(hours: int = 24, level: Optional[str] = None) -> dict[str, Any]:
    """获取告警列表"""
    monitor = get_system_monitor()
    alerts = monitor.get_recent_alerts(hours=hours)
    
    # 过滤级别
    if level:
        alerts = [a for a in alerts if a.level.value == level]
    
    return {
        "total": len(alerts),
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
    }


@router.get("/alerts", summary="获取告警列表")
async def get_alerts_endpoint(
    hours: int = 24,
    level: Optional[str] = None
) -> dict[str, Any]:
    """获取告警列表"""
    return await get_alerts(hours=hours, level=level)


async def get_alert_rules() -> dict[str, Any]:
    """获取告警规则"""
    monitor = get_system_monitor()
    rules = monitor._alert_rules
    
    return {
        "rules": [
            {
                "name": r.name,
                "description": r.description,
                "level": r.level.value,
                "cooldown_seconds": r.cooldown_seconds,
                "enabled": r.enabled,
            }
            for r in rules
        ],
        "total": len(rules),
    }


@router.get("/alert-rules", summary="获取告警规则")
async def get_alert_rules_endpoint() -> dict[str, Any]:
    """获取告警规则"""
    return await get_alert_rules()


async def enable_alert_rule(rule_name: str, user: User) -> dict[str, Any]:
    """启用告警规则"""
    monitor = get_system_monitor()
    
    for rule in monitor._alert_rules:
        if rule.name == rule_name:
            rule.enabled = True
            return {
                "success": True,
                "message": f"规则 '{rule_name}' 已启用",
            }
    
    raise HTTPException(status_code=404, detail=f"规则 '{rule_name}' 不存在")


@router.post("/alert-rules/{rule_name}/enable", summary="启用告警规则")
async def enable_alert_rule_endpoint(
    rule_name: str,
    user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """启用告警规则"""
    return await enable_alert_rule(rule_name, user)


async def disable_alert_rule(rule_name: str, user: User) -> dict[str, Any]:
    """禁用告警规则"""
    monitor = get_system_monitor()
    
    for rule in monitor._alert_rules:
        if rule.name == rule_name:
            rule.enabled = False
            return {
                "success": True,
                "message": f"规则 '{rule_name}' 已禁用",
            }
    
    raise HTTPException(status_code=404, detail=f"规则 '{rule_name}' 不存在")


@router.post("/alert-rules/{rule_name}/disable", summary="禁用告警规则")
async def disable_alert_rule_endpoint(
    rule_name: str,
    user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """禁用告警规则"""
    return await disable_alert_rule(rule_name, user)


# WebSocket 状态
async def get_websocket_status() -> dict[str, Any]:
    """获取WebSocket状态"""
    return {
        "total_connections": enhanced_manager.get_total_connections(),
        "online_users": enhanced_manager.get_online_users(),
        "rooms": list(enhanced_manager._rooms.keys()) if hasattr(enhanced_manager, '_rooms') else [],
    }


@router.get("/websocket-status", summary="获取WebSocket状态")
async def get_websocket_status_endpoint() -> dict[str, Any]:
    """获取WebSocket状态"""
    return await get_websocket_status()


# 系统信息
async def get_system_info() -> dict[str, Any]:
    """获取系统信息"""
    info = {
        "platform": "unknown",
        "platform_version": "unknown",
        "processor": "unknown",
        "python_version": "unknown",
        "memory": {},
        "disk": {},
        "cpu": {},
    }
    
    if _has_platform:
        info["platform"] = platform.system()
        info["platform_version"] = platform.version()
        info["processor"] = platform.processor()
        info["python_version"] = platform.python_version()
    
    if _has_psutil:
        # 内存信息
        memory = psutil.virtual_memory()
        info["memory"] = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent": memory.percent,
        }
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        info["disk"] = {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent,
        }
        
        # CPU信息
        info["cpu"] = {
            "percent": psutil.cpu_percent(interval=0.1),
            "count": psutil.cpu_count(),
        }
    
    return info


@router.get("/system-info", summary="获取系统信息")
async def get_system_info_endpoint() -> dict[str, Any]:
    """获取系统信息"""
    return await get_system_info()


# 数据库状态
async def get_database_status(db: AsyncSession) -> dict[str, Any]:
    """获取数据库状态"""
    try:
        # 执行简单查询测试连接
        result = await db.execute(text("SELECT 1"))
        row = result.fetchone()
        
        if row and row[0] == 1:
            # 获取数据库版本
            version_result = await db.execute(text("SELECT sqlite_version()"))
            version = version_result.scalar_one_or_none()
            
            return {
                "status": "healthy",
                "connection": "active",
                "version": version,
            }
        else:
            return {
                "status": "unhealthy",
                "connection": "error",
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connection": "failed",
            "error": str(e),
        }


@router.get("/database-status", summary="获取数据库状态")
async def get_database_status_endpoint(
    db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """获取数据库状态"""
    return await get_database_status(db)


# 缓存状态
async def get_cache_status() -> dict[str, Any]:
    """获取缓存状态"""
    settings = get_settings()
    
    if not settings.redis_url:
        return {
            "status": "not_configured",
            "message": "Redis未配置",
        }
    
    if not _has_redis:
        return {
            "status": "unavailable",
            "message": "Redis库未安装",
        }
    
    try:
        client = redis.from_url(str(settings.redis_url))  # type: ignore[attr-defined]
        if await client.ping():
            info = await client.info()
            return {
                "status": "healthy",
                "connection": "active",
                "memory": info.get("used_memory_human", "unknown"),
                "clients": info.get("connected_clients", 0),
            }
        else:
            return {
                "status": "unhealthy",
                "connection": "failed",
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connection": "error",
            "error": str(e),
        }


@router.get("/cache-status", summary="获取缓存状态")
async def get_cache_status_endpoint() -> dict[str, Any]:
    """获取缓存状态"""
    return await get_cache_status()


# 日报表
async def get_daily_report(date: Optional[str] = None) -> dict[str, Any]:
    """获取日报表"""
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    monitor = get_system_monitor()
    
    return {
        "date": date,
        "summary": {
            "api_requests": monitor.get_counter("api.total"),
            "errors": monitor.get_counter("api.error"),
            "ai_responses": monitor.get_counter("ai.response.total"),
        },
        "health_status": monitor.get_health_status()["status"],
    }


@router.get("/daily-report", summary="获取日报表")
async def get_daily_report_endpoint(
    date: Optional[str] = None
) -> dict[str, Any]:
    """获取日报表"""
    return await get_daily_report(date=date)
