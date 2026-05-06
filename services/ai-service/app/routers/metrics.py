"""AI服务监控指标路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.metrics import get_metrics_collector
from app.services.retrieval_cache import get_retrieval_cache_service

router = APIRouter(prefix="/metrics", tags=["监控指标"])


class MetricsResponse(BaseModel):
    timestamp: str
    llm: dict
    rag: dict
    agent: dict
    session: dict


class CacheStatsResponse(BaseModel):
    size: int
    max_size: int
    hits: int
    misses: int
    hit_rate: float
    evictions: int


class LLMConfigResponse(BaseModel):
    circuit_breaker_threshold: int
    circuit_breaker_timeout: int
    max_tokens: int
    temperature: float


@router.get("", response_model=MetricsResponse)
async def get_metrics():
    """获取所有监控指标"""
    try:
        collector = get_metrics_collector()
        return await collector.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache", response_model=CacheStatsResponse)
async def get_cache_stats():
    """获取缓存统计"""
    try:
        cache_service = get_retrieval_cache_service()
        return await cache_service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate")
async def invalidate_cache(pattern: Optional[str] = None):
    """使缓存失效"""
    try:
        cache_service = get_retrieval_cache_service()
        await cache_service.invalidate(pattern)
        return {"message": "Cache invalidated", "pattern": pattern}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_metrics():
    """重置所有指标"""
    try:
        collector = get_metrics_collector()
        await collector.reset()
        return {"message": "Metrics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=LLMConfigResponse)
async def get_llm_config():
    """获取LLM配置"""
    from app.config.settings import get_settings
    settings = get_settings()
    return LLMConfigResponse(
        circuit_breaker_threshold=settings.circuit_breaker_threshold,
        circuit_breaker_timeout=settings.circuit_breaker_timeout,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature
    )
