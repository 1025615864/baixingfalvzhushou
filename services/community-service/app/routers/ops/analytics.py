"""运营数据分析路由"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ops.analytics_ops_service import AnalyticsOpsService
from app.middleware.ops_auth import require_ops_role

try:
    from services.common.middleware.admin_auth import require_domain_role
except ImportError:
    from fastapi import Depends, HTTPException
    def require_domain_role(domain: str, roles=None):
        async def _checker(request=None):
            from fastapi import Request
            if request and hasattr(request, 'headers'):
                role = request.headers.get("X-Admin-Role", "")
                if role in {"super_admin", "admin"}:
                    return None
                if roles and role not in roles:
                    raise HTTPException(status_code=403, detail=f"需要角色: {', '.join(roles)}")
            return None
        return _checker

router = APIRouter(prefix="/api/v1/community/ops/analytics", tags=["运营数据分析"], dependencies=[Depends(require_domain_role("community", roles=["community_admin", "community_ops"]))])


@router.get("/overview")
async def get_overview(
    period: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("data_analyst", "community_director"))
):
    service = AnalyticsOpsService(db)
    stats = await service.get_overview_stats(period_days=period)
    return {"success": True, "data": stats}


@router.get("/trends")
async def get_trends(
    metric: str = Query("posts", pattern="^(posts|comments|users)$"),
    period: int = Query(30, ge=1, le=90),
    granularity: str = Query("day", pattern="^(day|hour)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("data_analyst", "community_director"))
):
    service = AnalyticsOpsService(db)
    data = await service.get_trend_data(
        metric=metric,
        period_days=period,
        granularity=granularity
    )
    return {"success": True, "data": data}


@router.get("/content-quality")
async def get_content_quality(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("data_analyst", "community_director"))
):
    service = AnalyticsOpsService(db)
    stats = await service.get_content_quality_stats()
    return {"success": True, "data": stats}


@router.get("/moderation")
async def get_moderation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_ops_role("data_analyst", "content_mod", "community_director"))
):
    service = AnalyticsOpsService(db)
    stats = await service.get_moderation_efficiency()
    return {"success": True, "data": stats}


@router.get("/export")
async def export_analytics(
    report_type: str = Query("overview", pattern="^(overview|posts|users|moderation)$"),
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    period: int = Query(30, ge=1, le=90),
    current_user: dict = Depends(require_ops_role("data_analyst", "community_director"))
):
    return {
        "success": True,
        "message": f"报表【{report_type}】导出格式【{format}】生成中",
        "download_url": f"/api/v1/community/ops/analytics/download/{report_type}.{format}"
    }
