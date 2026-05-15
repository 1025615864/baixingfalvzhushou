from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import SearchIndex, HotSearch, SearchLog

try:
    from services.common.middleware.admin_auth import get_admin_user, AdminUser, require_domain_role
except ImportError:
    from fastapi import Request

    class AdminUser:
        def __init__(self, user_id: int = 0, role: str = "admin", permissions=None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in {"super_admin", "admin"}

    async def get_admin_user(request: Request = None):
        if request:
            user_id = int(request.headers.get("X-Admin-User-Id", "0"))
            role = request.headers.get("X-Admin-Role", "admin")
            permissions = request.headers.get("X-Admin-Permissions", "").split(",")
            return AdminUser(user_id=user_id, role=role, permissions=permissions)
        return AdminUser()

    def require_domain_role(domain: str, roles=None):
        async def _checker(admin: AdminUser = Depends(get_admin_user)):
            if admin.is_super_admin:
                return admin
            if roles and admin.role not in roles:
                raise HTTPException(status_code=403, detail=f"需要角色: {', '.join(roles)}")
            return admin
        return _checker


admin_router = APIRouter(dependencies=[Depends(require_domain_role("search", roles=["search_admin"]))])


class HotSearchUpdate(BaseModel):
    status: Optional[str] = None


async def _write_audit_log(
    db: AsyncSession,
    admin: AdminUser,
    action: str,
    target_type: str = None,
    target_id: int = None,
    comment: str = None,
    extra_data: dict = None,
):
    from ..models import SearchAuditLog
    log = SearchAuditLog(
        operator_id=admin.user_id,
        operator_name=str(admin.user_id),
        action=action,
        target_type=target_type,
        target_id=target_id,
        comment=comment,
        extra_data=extra_data,
    )
    db.add(log)


@admin_router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = today_start - timedelta(days=7)

    total_searches_result = await db.execute(select(func.count(SearchLog.id)))
    total_searches = total_searches_result.scalar() or 0

    today_searches_result = await db.execute(
        select(func.count(SearchLog.id)).where(SearchLog.created_at >= today_start)
    )
    today_searches = today_searches_result.scalar() or 0

    hot_keywords_result = await db.execute(
        select(SearchLog.query, func.count(SearchLog.id).label("cnt"))
        .where(SearchLog.created_at >= seven_days_ago)
        .group_by(SearchLog.query)
        .order_by(func.count(SearchLog.id).desc())
        .limit(10)
    )
    hot_keywords = [
        {"keyword": row.query, "count": row.cnt} for row in hot_keywords_result.all()
    ]

    type_dist_result = await db.execute(
        select(SearchLog.search_type, func.count(SearchLog.id).label("cnt"))
        .where(SearchLog.created_at >= seven_days_ago)
        .group_by(SearchLog.search_type)
    )
    search_type_distribution = [
        {"type": row.search_type, "count": row.cnt} for row in type_dist_result.all()
    ]

    zero_result_count_result = await db.execute(
        select(func.count(SearchLog.id)).where(
            SearchLog.result_count == 0,
            SearchLog.created_at >= seven_days_ago,
        )
    )
    zero_result_count = zero_result_count_result.scalar() or 0

    recent_total_result = await db.execute(
        select(func.count(SearchLog.id)).where(SearchLog.created_at >= seven_days_ago)
    )
    recent_total = recent_total_result.scalar() or 0
    zero_result_rate = round(zero_result_count / recent_total, 4) if recent_total > 0 else 0.0

    return {
        "total_searches": total_searches,
        "today_searches": today_searches,
        "hot_keywords": hot_keywords,
        "search_type_distribution": search_type_distribution,
        "zero_result_rate": zero_result_rate,
    }


@admin_router.get("/stats")
async def search_stats(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            filters.append(SearchLog.created_at >= sd)
        except ValueError:
            raise HTTPException(status_code=400, detail="start_date 格式错误，应为 YYYY-MM-DD")
    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc, hour=23, minute=59, second=59
            )
            filters.append(SearchLog.created_at <= ed)
        except ValueError:
            raise HTTPException(status_code=400, detail="end_date 格式错误，应为 YYYY-MM-DD")

    base_query = select(SearchLog)
    for f in filters:
        base_query = base_query.where(f)

    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = total_result.scalar() or 0

    avg_result_count_query = select(func.avg(SearchLog.result_count))
    for f in filters:
        avg_result_count_query = avg_result_count_query.where(f)
    avg_result = await db.execute(avg_result_count_query)
    avg_result_count = round(avg_result.scalar() or 0, 2)

    daily_query = (
        select(
            func.date_trunc("day", SearchLog.created_at).label("day"),
            func.count(SearchLog.id).label("count"),
        )
        .group_by(func.date_trunc("day", SearchLog.created_at))
        .order_by(func.date_trunc("day", SearchLog.created_at).desc())
        .limit(30)
    )
    for f in filters:
        daily_query = daily_query.where(f)
    daily_result = await db.execute(daily_query)
    daily_stats = [
        {"date": row.day.isoformat() if row.day else None, "count": row.count}
        for row in daily_result.all()
    ]

    return {
        "total_searches": total,
        "avg_result_count": avg_result_count,
        "daily_stats": daily_stats,
    }


@admin_router.get("/hot-searches")
async def list_hot_searches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(HotSearch)
    if status:
        query = query.where(HotSearch.status == status)
    query = query.order_by(HotSearch.search_count.desc())

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": h.id,
                "keyword": h.keyword,
                "search_count": h.search_count,
                "status": h.status,
                "updated_at": h.updated_at.isoformat() if h.updated_at else None,
            }
            for h in items
        ],
    }


@admin_router.put("/hot-searches/{hot_search_id}")
async def update_hot_search(
    hot_search_id: int,
    body: HotSearchUpdate,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(HotSearch).where(HotSearch.id == hot_search_id))
    hot_search = result.scalar_one_or_none()
    if not hot_search:
        raise HTTPException(status_code=404, detail="热搜词不存在")

    if body.status is not None:
        old_status = hot_search.status
        hot_search.status = body.status
        await _write_audit_log(
            db,
            admin,
            action="update_hot_search_status",
            target_type="hot_search",
            target_id=hot_search_id,
            comment=f"状态变更: {old_status} -> {body.status}",
        )

    await db.flush()
    return {"id": hot_search.id, "keyword": hot_search.keyword, "status": hot_search.status}


@admin_router.delete("/hot-searches/{hot_search_id}")
async def delete_hot_search(
    hot_search_id: int,
    admin: AdminUser = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(HotSearch).where(HotSearch.id == hot_search_id))
    hot_search = result.scalar_one_or_none()
    if not hot_search:
        raise HTTPException(status_code=404, detail="热搜词不存在")

    await _write_audit_log(
        db,
        admin,
        action="delete_hot_search",
        target_type="hot_search",
        target_id=hot_search_id,
        comment=f"删除热搜词: {hot_search.keyword}",
    )
    await db.delete(hot_search)
    await db.flush()
    return {"detail": "已删除"}


@admin_router.get("/search-history")
async def list_search_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    query_text: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SearchLog)
    if user_id is not None:
        stmt = stmt.where(SearchLog.user_id == user_id)
    if query_text:
        stmt = stmt.where(SearchLog.query.ilike(f"%{query_text}%"))

    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar() or 0

    stmt = stmt.order_by(SearchLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": s.id,
                "user_id": s.user_id,
                "query": s.query,
                "search_type": s.search_type,
                "result_count": s.result_count,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in items
        ],
    }


@admin_router.get("/suggestions")
async def list_suggestions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SearchIndex.item_type, SearchIndex.title, func.count(SearchIndex.id).label("cnt"))
        .where(SearchIndex.status == "active")
        .group_by(SearchIndex.item_type, SearchIndex.title)
        .order_by(func.count(SearchIndex.id).desc())
    )

    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar() or 0

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {"type": row.item_type, "title": row.title, "count": row.cnt}
            for row in items
        ],
    }


@admin_router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    from ..models import SearchAuditLog

    stmt = select(SearchAuditLog)
    if action:
        stmt = stmt.where(SearchAuditLog.action == action)

    count_result = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count_result.scalar() or 0

    stmt = stmt.order_by(SearchAuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": a.id,
                "operator_id": a.operator_id,
                "operator_name": a.operator_name,
                "action": a.action,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "comment": a.comment,
                "extra_data": a.extra_data,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in items
        ],
    }
