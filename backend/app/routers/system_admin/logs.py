"""操作日志路由"""

import json
from typing import Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.system import AdminLog, LogAction, LogModule
from ...models.user import User
from ...utils.deps import require_admin
from ...utils.rate_limiter import get_client_ip

router = APIRouter(prefix="/logs", tags=["操作日志"])


class LogResponse(BaseModel):
    """日志响应"""
    id: int
    user_id: int | None
    username: str | None
    action: str
    module: str
    description: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class LogListResponse(BaseModel):
    """日志列表响应"""
    items: list[LogResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=LogListResponse)
async def get_admin_logs(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(ge=1, default=1),
    page_size: int = Query(ge=1, le=100, default=20),
    action: str | None = None,
    module: str | None = None,
    user_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """获取操作日志列表"""
    query = select(AdminLog)
    count_query = select(func.count(AdminLog.id))

    if action:
        query = query.where(AdminLog.action == action)
        count_query = count_query.where(AdminLog.action == action)
    if module:
        query = query.where(AdminLog.module == module)
        count_query = count_query.where(AdminLog.module == module)
    if user_id:
        query = query.where(AdminLog.user_id == user_id)
        count_query = count_query.where(AdminLog.user_id == user_id)
    if start_date:
        query = query.where(AdminLog.created_at >= start_date)
        count_query = count_query.where(AdminLog.created_at >= start_date)
    if end_date:
        query = query.where(AdminLog.created_at <= end_date)
        count_query = count_query.where(AdminLog.created_at <= end_date)

    query = query.order_by(desc(AdminLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()
    total = await db.scalar(count_query)

    return LogListResponse(
        items=[
            LogResponse(
                id=log.id,
                user_id=log.user_id,
                username=(
                    log.user.username if getattr(
                        log, "user", None) is not None else None),
                action=str(log.action),
                module=str(log.module),
                description=log.description,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=int(total or 0),
        page=page,
        page_size=page_size,
    )


@router.get("/actions", response_model=list[str])
async def get_log_actions(
        _current_user: Annotated[User, Depends(require_admin)]):
    """获取日志操作类型列表"""
    return sorted(
        [value for value in LogAction.__dict__.values() if isinstance(value, str)]
    )


@router.get("/modules", response_model=list[str])
async def get_log_modules(
        _current_user: Annotated[User, Depends(require_admin)]):
    """获取日志模块列表"""
    return sorted(
        [value for value in LogModule.__dict__.values() if isinstance(value, str)]
    )


@router.get("/stats")
async def get_log_stats(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(default=7, ge=1, le=90),
):
    """获取日志统计"""
    from datetime import timedelta

    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    # 按操作类型统计
    action_query = (
        select(AdminLog.action, func.count(AdminLog.id))
        .where(AdminLog.created_at >= start_date)
        .group_by(AdminLog.action)
    )
    action_result = await db.execute(action_query)
    action_stats = {str(row[0]): row[1] for row in action_result.all()}

    # 按模块统计
    module_query = (
        select(AdminLog.module, func.count(AdminLog.id))
        .where(AdminLog.created_at >= start_date)
        .group_by(AdminLog.module)
    )
    module_result = await db.execute(module_query)
    module_stats = {str(row[0]): row[1] for row in module_result.all()}

    # 按天统计
    daily_query = (
        select(
            func.date(AdminLog.created_at),
            func.count(AdminLog.id)
        )
        .where(AdminLog.created_at >= start_date)
        .group_by(func.date(AdminLog.created_at))
        .order_by(func.date(AdminLog.created_at))
    )
    daily_result = await db.execute(daily_query)
    daily_stats = {str(row[0]): row[1] for row in daily_result.all()}

    return {
        "period_days": days,
        "by_action": action_stats,
        "by_module": module_stats,
        "by_day": daily_stats,
    }


async def _log_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    module: str,
    target_id: int | None = None,
    target_type: str | None = None,
    description: str | None = None,
    extra_data: dict[str, object] | None = None,
    request: Request | None = None,
) -> None:
    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")[:500]

    log = AdminLog(
        user_id=int(user_id),
        action=str(action),
        module=str(module),
        target_id=target_id,
        target_type=target_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_data=json.dumps(extra_data,
                              ensure_ascii=False) if extra_data else None,
    )
    db.add(log)


async def log_admin_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    module: str,
    target_id: int | None = None,
    description: str | None = None,
    request: Request | None = None,
) -> None:
    await _log_action(
        db=db,
        user_id=int(user_id),
        action=action,
        module=module,
        target_id=target_id,
        description=description,
        request=request,
    )


__all__ = ["router", "log_admin_action"]
