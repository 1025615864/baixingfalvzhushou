"""社区服务监控指标路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.metrics import get_metrics_collector

router = APIRouter(prefix="/metrics", tags=["监控指标"])


class MetricsResponse(BaseModel):
    timestamp: str
    post: dict
    api: dict
    cache: dict
    kafka: dict


@router.get("/", response_model=MetricsResponse)
async def get_metrics():
    try:
        collector = get_metrics_collector()
        return await collector.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_metrics():
    try:
        collector = get_metrics_collector()
        await collector.reset()
        return {"message": "Metrics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
