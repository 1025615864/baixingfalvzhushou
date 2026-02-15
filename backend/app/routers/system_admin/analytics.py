"""数据统计路由"""

from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.system import SystemConfig
from ...models.user import User
from ...utils.deps import require_admin

router = APIRouter(prefix="/analytics", tags=["数据统计"])


@router.get("/overview")
async def get_analytics_overview(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=90),
):
    """获取数据概览"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # 用户统计
    user_count = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(
        select(func.count(User.id)).where(User.is_active)
    )

    # 配置统计
    config_count = await db.scalar(select(func.count(SystemConfig.id)))

    return {
        "period_days": days,
        "users": {
            "total": user_count,
            "active": active_users,
        },
        "configs": config_count,
    }


@router.get("/users")
async def get_user_stats(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=30, ge=1, le=90),
):
    """获取用户统计"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    total = await db.scalar(select(func.count(User.id)))
    new_users = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= start_date)
    )
    active = await db.scalar(
        select(func.count(User.id)).where(User.is_active)
    )

    return {
        "total": total,
        "new_in_period": new_users,
        "active": active,
    }


@router.get("/system")
async def get_system_stats(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取系统统计"""
    config_count = await db.scalar(select(func.count(SystemConfig.id)))

    return {
        "configs": config_count,
    }
