"""管理领域路由"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...schemas import LawyerResponse
from ...middleware.auth import require_permissions
from ...shared.permissions import Permission

router = APIRouter(prefix="/admin", tags=["管理"])


@router.get("/stats/platform")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.ADMIN_STATS)),
):
    from ...services.admin_service import AdminService
    service = AdminService(db)
    stats = await service.get_platform_stats()
    return stats


@router.get("/lawyers")
async def list_all_lawyers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.ADMIN_LAWYER_ALL)),
):
    from ...services.admin_service import AdminService
    service = AdminService(db)
    lawyers, total = await service.list_all_lawyers(
        page=page,
        page_size=page_size,
        status=status,
    )
    return {
        "items": [LawyerResponse.model_validate(l) for l in lawyers],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/lawyers/{lawyer_id}/suspend")
async def suspend_lawyer(
    lawyer_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.ADMIN_LAWYER_ALL)),
):
    from ...services.admin_service import AdminService
    service = AdminService(db)
    lawyer = await service.suspend_lawyer(lawyer_id, reason)
    if not lawyer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="律师不存在")
    return {"message": "律师已暂停"}


@router.patch("/lawyers/{lawyer_id}/reactivate")
async def reactivate_lawyer(
    lawyer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.ADMIN_LAWYER_ALL)),
):
    from ...services.admin_service import AdminService
    service = AdminService(db)
    lawyer = await service.reactivate_lawyer(lawyer_id)
    if not lawyer:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="律师不存在")
    return {"message": "律师已重新激活"}


@router.get("/consultations/stats")
async def get_consultation_stats(
    start_date: datetime = None,
    end_date: datetime = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.ADMIN_STATS)),
):
    from ...services.admin_service import AdminService
    service = AdminService(db)
    stats = await service.get_consultation_stats(start_date, end_date)
    return stats


@router.get("/reports/lawyer-ratings")
async def get_lawyer_ratings_report(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.ADMIN_STATS)),
):
    from ...services.admin_service import AdminService
    service = AdminService(db)
    report = await service.get_lawyer_ratings_report()
    return report