"""漏斗分析 API 路由

提供漏斗配置、事件追踪和效果分析功能。
"""
from typing import Annotated, Any
from fastapi import APIRouter, Depends, Query, HTTPException, Body

from ..models.user import User
from ..schemas.funnel import FunnelCreateRequest, FunnelTrackRequest
from ..services.funnel_analysis import (
    funnel_service,
    create_funnel,
    track_funnel_event,
    analyze_funnel,
    get_funnel_stats as get_funnel_stats_func,
)
from ..utils.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/funnel", tags=["漏斗分析"])


@router.post("/funnels")
async def create_funnel_config(
    request: FunnelCreateRequest = Body(..., description="漏斗配置信息"),
) -> dict[str, Any]:
    """创建漏斗配置"""
    # Convert Pydantic models to dict/list format expected by service
    steps_list = [step.model_dump() for step in request.steps]
    result = await create_funnel(request.funnel_id, request.name, steps_list)
    return result


@router.get("/funnels")
async def list_funnels() -> dict[str, Any]:
    """列出所有漏斗"""
    funnels = funnel_service._configurator.list_funnels()
    return {"funnels": funnels}


@router.get("/funnels/{funnel_id}")
async def get_funnel_config(funnel_id: str) -> dict[str, Any]:
    """获取漏斗配置"""
    funnel = funnel_service._configurator.get_funnel(funnel_id)
    if not funnel:
        raise HTTPException(status_code=404, detail="漏斗不存在")
    return funnel


@router.post("/track")
async def track_funnel_event_route(
    request: FunnelTrackRequest,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
):
    """追踪漏斗事件"""
    user_id = current_user.id if current_user else 0
    await track_funnel_event(user_id, request.funnel_id, request.step_id)
    return {"message": "Event tracked"}


@router.get("/funnels/{funnel_id}/analysis")
async def get_funnel_analysis(
    funnel_id: str,
    start_date: str | None = Query(None, description="开始日期"),
    end_date: str | None = Query(None, description="结束日期"),
) -> dict[str, Any]:
    """获取漏斗分析结果"""
    result = await analyze_funnel(funnel_id, start_date, end_date)
    return result


@router.get("/funnels/{funnel_id}/drop-off")
async def get_drop_off_points(funnel_id: str) -> dict[str, Any]:
    """获取流失点分析"""
    points = funnel_service.identify_drop_off_points(funnel_id)
    return {"points": points}


@router.get("/funnels/{funnel_id}/progress")
async def get_user_funnel_progress(
    funnel_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """获取用户在漏斗中的进度"""
    progress = funnel_service._tracker.get_user_progress(current_user.id, funnel_id)
    if not progress:
        return {"status": "not_started"}
    return progress


@router.get("/stats")
async def get_funnel_stats() -> dict[str, Any]:
    """获取漏斗统计数据"""
    stats = await get_funnel_stats_func()
    return stats
