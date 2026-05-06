"""数据看板路由"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.dashboard_service import DashboardService
from ..middleware.auth import AuthMiddleware, AuthUser
from ..clients import user_service_client

router = APIRouter(prefix="/dashboard", tags=["数据看板"])

auth_middleware = AuthMiddleware(user_client=user_service_client)


@router.get("/overview")
async def get_overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role not in ("admin", "moderator"):
        return {"success": False, "error": "需要管理员权限"}

    service = DashboardService(db)
    stats = await service.get_overview_stats()
    return {"success": True, "data": stats}


@router.get("/trending-topics")
async def get_trending_topics(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role not in ("admin", "moderator"):
        return {"success": False, "error": "需要管理员权限"}

    service = DashboardService(db)
    topics = await service.get_trending_topics(limit=limit)
    return {"success": True, "data": topics}


@router.get("/user-activity")
async def get_user_activity(
    request: Request,
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role not in ("admin", "moderator"):
        return {"success": False, "error": "需要管理员权限"}

    service = DashboardService(db)
    activity = await service.get_user_activity_stats(days=days)
    return {"success": True, "data": activity}


@router.get("/top-posts")
async def get_top_posts(
    request: Request,
    metric: str = Query("views", regex="^(views|likes|comments|hot)$"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role not in ("admin", "moderator"):
        return {"success": False, "error": "需要管理员权限"}

    service = DashboardService(db)
    posts = await service.get_top_posts(metric=metric, limit=limit)
    return {"success": True, "data": posts}


@router.get("/category-distribution")
async def get_category_distribution(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role not in ("admin", "moderator"):
        return {"success": False, "error": "需要管理员权限"}

    service = DashboardService(db)
    distribution = await service.get_category_distribution()
    return {"success": True, "data": distribution}
