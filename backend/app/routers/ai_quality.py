"""
AI质量统计接口

提供AI咨询质量监控的统计接口：
- /api/system/ai-quality/stats - 获取整体统计
- /api/system/ai-quality/logs - 获取最近日志
- /api/system/ai-quality/reset - 重置统计数据（仅开发环境）
- /api/system/ai-quality/prometheus - Prometheus指标
- /api/system/ai-quality/dashboard - 仪表板数据
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from starlette.responses import PlainTextResponse

from app.middleware.ai_quality_middleware import (
    get_ai_metrics,
    get_ai_logger,
    get_ai_quality_prometheus_exporter,
    AIQualityMetrics,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system/ai-quality", tags=["AI质量监控"])


class AIQualityStatsResponse(BaseModel):
    """AI质量统计响应"""
    total_conversations: int = Field(..., description="总对话数")
    successful_conversations: int = Field(..., description="成功对话数")
    error_count: int = Field(..., description="错误次数")
    success_rate: float = Field(..., description="成功率(%)")

    response_time: dict = Field(..., description="响应时间统计")
    quality_score: dict = Field(..., description="质量评分统计")
    error_distribution: dict = Field(..., description="错误分布")
    topic_distribution: dict = Field(..., description="话题分布")
    tool_usage: dict = Field(..., description="工具使用分布")

    positive_feedback: int = Field(..., description="正面反馈数")
    negative_feedback: int = Field(..., description="负面反馈数")
    helpful_responses: int = Field(..., description="有用回复数")
    unhelpful_responses: int = Field(..., description="无用回复数")

    timestamp: str = Field(..., description="统计时间")


class AILogEntry(BaseModel):
    """AI日志条目"""
    request_id: str
    session_id: Optional[str]
    user_id: Optional[int]
    message_length: int
    response_length: int
    response_time_ms: int
    quality_score: Optional[int]
    quality_level: Optional[str]
    was_helpful: Optional[bool]
    topics: list
    tools_used: list
    error_type: Optional[str]
    timestamp: str
    level: str


class AILogsResponse(BaseModel):
    """AI日志列表响应"""
    logs: Sequence[dict[str, Any]]  # 使用Sequence避免类型不兼容问题
    total: int
    limit: int


class ResetResponse(BaseModel):
    """重置响应"""
    message: str
    previous_stats: dict


@router.get("/stats", response_model=AIQualityStatsResponse)
async def get_ai_quality_stats():
    """
    获取AI质量统计信息

    返回AI咨询的整体质量指标：
    - 对话总数与成功率
    - 响应时间分布（P50/P95/平均值）
    - 质量评分分布与满意度
    - 错误类型分布
    - 话题与工具使用分布
    """
    metrics = get_ai_metrics()
    stats = metrics.get_stats()

    total = stats["total_conversations"]
    success = stats["successful_conversations"]
    success_rate = round(success / total * 100, 2) if total > 0 else 0

    return AIQualityStatsResponse(
        total_conversations=total,
        successful_conversations=success,
        error_count=stats["counters"].get("total_errors", 0),
        success_rate=success_rate,
        response_time=stats["response_time"],
        quality_score=stats["quality_score"],
        error_distribution=stats["errors"],
        topic_distribution=_get_topic_distribution(stats["counters"]),
        tool_usage=_get_tool_usage(stats["counters"]),
        positive_feedback=stats["counters"].get("positive_feedback", 0),
        negative_feedback=stats["counters"].get("negative_feedback", 0),
        helpful_responses=stats["counters"].get("helpful_responses", 0),
        unhelpful_responses=stats["counters"].get("unhelpful_responses", 0),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/logs", response_model=AILogsResponse)
async def get_ai_quality_logs(
    limit: int = Query(default=100, ge=1, le=1000, description="返回日志数量")
):
    """
    获取AI咨询最近日志

    返回最近的AI对话日志，支持按数量限制
    """
    logger_service = get_ai_logger()
    logs = logger_service.get_recent_logs(limit)

    return AILogsResponse(
        logs=logs,
        total=len(logs),
        limit=limit,
    )


@router.post("/reset", response_model=ResetResponse)
async def reset_ai_quality_stats():
    """
    重置AI质量统计数据

    ⚠️ 仅限开发/测试环境使用，生产环境禁止调用
    """
    import os

    # 生产环境禁止重置
    if os.getenv("DEBUG", "true").lower() != "true":
        raise HTTPException(
            status_code=403,
            detail="Reset operation is not allowed in production environment"
        )

    metrics = get_ai_metrics()
    previous_stats = metrics.get_stats()

    metrics.reset()

    logger.warning("AI quality stats have been reset")

    return ResetResponse(
        message="AI quality statistics have been reset",
        previous_stats={
            "total_conversations": previous_stats["total_conversations"],
            "successful_conversations": previous_stats["successful_conversations"],
            "avg_quality_score": previous_stats["quality_score"]["avg"],
        })


@router.get("/health")
async def ai_quality_health():
    """
    AI质量监控健康检查

    检查AI质量监控系统是否正常运行
    """
    metrics = get_ai_metrics()
    stats = metrics.get_stats()

    return {
        "status": "healthy",
        "total_conversations": stats["total_conversations"],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/prometheus")
async def get_ai_quality_prometheus_metrics():
    """
    AI质量监控Prometheus指标

    返回Prometheus格式的指标数据，可用于Grafana监控
    """
    from fastapi.responses import PlainTextResponse
    from app.middleware.ai_quality_middleware import get_ai_quality_prometheus_exporter

    exporter = get_ai_quality_prometheus_exporter()
    metrics_text = exporter.render_metrics()

    return PlainTextResponse(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/dashboard")
async def get_ai_quality_dashboard():
    """
    AI质量监控仪表板数据

    返回适合前端仪表板展示的数据结构
    """
    metrics = get_ai_metrics()
    stats = metrics.get_stats()

    # 计算趋势（简化版，实际应该从时间序列数据计算）
    trend = {
        "response_time_trend": "stable",
        "quality_trend": "stable",
        "satisfaction_trend": "stable",
    }

    return {
        "summary": {
            "total_conversations": stats["total_conversations"],
            "success_rate": round(
                stats["successful_conversations"] /
                stats["total_conversations"] * 100, 2
            )
            if stats["total_conversations"] > 0
            else 0,
            "avg_response_time_ms": stats["response_time"]["avg_ms"],
            "avg_quality_score": stats["quality_score"]["avg"],
            "satisfaction_rate": stats["quality_score"]["satisfaction_rate"],
        },
        "response_time": {
            "p50_ms": stats["response_time"]["p50_ms"],
            "p95_ms": stats["response_time"]["p95_ms"],
            "p99_ms": stats["response_time"]["p99_ms"],
            "avg_ms": stats["response_time"]["avg_ms"],
        },
        "quality_distribution": stats["quality_score"]["distribution"],
        "topic_distribution": _get_topic_distribution(stats["counters"]),
        "tool_usage": _get_tool_usage(stats["counters"]),
        "error_distribution": stats["errors"],
        "feedback": {
            "positive": stats["counters"].get("positive_feedback", 0),
            "negative": stats["counters"].get("negative_feedback", 0),
            "helpful": stats["counters"].get("helpful_responses", 0),
            "unhelpful": stats["counters"].get("unhelpful_responses", 0),
        },
        "trend": trend,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def _get_topic_distribution(counters: dict) -> dict:
    """提取话题分布"""
    topic_dist = {}
    for key, value in counters.items():
        if key.startswith("topic_"):
            topic_name = key[6:]  # 去掉 "topic_" 前缀
            topic_dist[topic_name] = value
    return topic_dist


def _get_tool_usage(counters: dict) -> dict:
    """提取工具使用分布"""
    tool_usage = {}
    for key, value in counters.items():
        if key.startswith("tool_"):
            tool_name = key[5:]  # 去掉 "tool_" 前缀
            tool_usage[tool_name] = value
    return tool_usage


# 使用示例
"""
# 启动后访问
GET /api/system/ai-quality/stats  - 获取统计信息
GET /api/system/ai-quality/logs   - 获取最近日志
POST /api/system/ai-quality/reset - 重置统计（仅开发环境）
GET /api/system/ai-quality/health - 健康检查
"""
