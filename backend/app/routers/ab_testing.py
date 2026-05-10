"""A/B 测试 API 路由

提供实验创建、流量分配和效果统计功能。
"""
from typing import Annotated, Any
from fastapi import APIRouter, Depends, Query, HTTPException, Path

from ..models.user import User
from ..services.ab_testing import (
    ab_test_service,
    create_experiment,
    assign_variant,
    analyze_experiment,
)
from ..utils.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/ab", tags=["A/B 测试"])


@router.post("/experiments")
async def create_ab_experiment(
    current_user: Annotated[User, Depends(get_current_user)],
    experiment_id: str = Query(..., description="实验ID"),
    name: str = Query(..., description="实验名称"),
    variants: str = Query(..., description="变体列表 JSON 数组"),
    traffic_percentage: int = Query(
        default=100, ge=0, le=100, description="流量百分比"),
) -> dict[str, Any]:
    """创建 A/B 测试实验"""
    import json
    try:
        variants_list = json.loads(variants)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="variants 格式无效")

    result = await create_experiment(
        experiment_id=experiment_id,
        name=name,
        variants=variants_list,
        traffic_percentage=traffic_percentage,
    )
    return result


@router.get("/experiments")
async def list_ab_experiments() -> dict[str, Any]:
    """列出所有实验"""
    experiments = ab_test_service._configurator.list_experiments()
    return {"experiments": experiments}


@router.get("/experiments/{experiment_id}")
async def get_ab_experiment(experiment_id: str) -> dict[str, Any]:
    """获取实验详情"""
    experiment = ab_test_service._configurator.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="实验不存在")
    return experiment


@router.post("/experiments/{experiment_id}/status")
async def update_ab_experiment_status(
    current_user: Annotated[User, Depends(get_current_user)],
    experiment_id: str,
    status: str = Query(..., description="状态: draft/running/paused/completed"),
) -> dict[str, Any]:
    """更新实验状态"""
    result = ab_test_service._configurator.update_experiment_status(
        experiment_id, status)
    return result


@router.post("/assign")
async def assign_ab_variant(
    experiment_id: str = Query(..., description="实验ID"),
    variants: str = Query(..., description="变体列表 JSON 数组"),
    traffic_percentage: int = Query(
        default=100, ge=0, le=100, description="流量百分比"),
    current_user: Annotated[User | None, Depends(
        get_current_user_optional)] = None,
) -> dict[str, Any]:
    """为用户分配实验变体"""
    import json
    try:
        variants_list = json.loads(variants)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="variants 格式无效")

    user_id = current_user.id if current_user else 0
    result = await assign_variant(
        user_id=user_id,
        experiment_id=experiment_id,
        variants=variants_list,
        traffic_percentage=traffic_percentage,
    )
    return result


@router.get("/experiments/{experiment_id}/analysis")
async def get_ab_experiment_analysis(experiment_id: str) -> dict[str, Any]:
    """获取实验分析结果"""
    result = await analyze_experiment(experiment_id)
    return result


@router.post("/experiments/{experiment_id}/metric")
async def record_ab_metric(
    current_user: Annotated[User, Depends(get_current_user)],
    experiment_id: str = Path(..., description="实验ID"),
    metric_name: str = Query(..., description="指标名称"),
    value: float = Query(..., description="指标值"),
) -> dict[str, Any]:
    """记录实验指标"""
    result = ab_test_service.record_metric(
        user_id=current_user.id,
        experiment_id=experiment_id,
        metric_name=metric_name,
        value=value,
    )
    return result


@router.get("/stats")
async def get_ab_stats() -> dict[str, Any]:
    """获取实验统计信息"""
    return ab_test_service.get_experiment_stats()
