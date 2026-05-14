"""管理后台路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.lawyer_service import LawyerService
from ..services.consultation_service import ConsultationService
from ..services.appointment_service import AppointmentService
from ..schemas.response import ApiResponse, PaginatedData

try:
    from services.common.middleware.admin_auth import (
        get_admin_user, AdminUser, require_domain_role,
    )
except ImportError:
    import os
    from fastapi import HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from typing import List, Set

    _security = HTTPBearer(auto_error=False)

    GLOBAL_ADMIN_ROLES = {"super_admin", "admin"}

    DOMAIN_ROLES: dict[str, Set[str]] = {
        "global": {"super_admin", "admin"},
        "legal": {"legal_admin", "legal_ops", "lawfirm_owner"},
    }

    class AdminUser:
        def __init__(self, user_id: int, role: str, permissions: Optional[List[str]] = None):
            self.user_id = user_id
            self.role = role
            self.permissions = permissions or []
            self.is_super_admin = role in GLOBAL_ADMIN_ROLES

        def has_domain_access(self, domain: str) -> bool:
            if self.is_super_admin:
                return True
            return self.role in DOMAIN_ROLES.get(domain, set())

    async def get_admin_user(
        credentials: HTTPAuthorizationCredentials = Depends(_security),
    ) -> AdminUser:
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证凭据")
        if os.getenv("DISABLE_AUTH", "").lower() in {"1", "true", "yes"}:
            return AdminUser(user_id=0, role="admin")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="认证服务不可用")

    def require_domain_role(domain: str, roles: Optional[List[str]] = None):
        async def domain_checker(admin: AdminUser = Depends(get_admin_user)):
            if admin.is_super_admin:
                return admin
            if not admin.has_domain_access(domain):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要 {domain} 域管理角色，当前角色: {admin.role}",
                )
            if roles and admin.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要角色: {', '.join(roles)}，当前角色: {admin.role}",
                )
            return admin
        return domain_checker

router = APIRouter()


class AdminStatsResponse(BaseModel):
    total_lawyers: int
    verified_lawyers: int
    pending_lawyers: int
    total_consultations: int
    active_consultations: int


class LawyerVerificationRequest(BaseModel):
    lawyer_id: int
    action: str


@router.get("/stats")
async def get_stats(
    current_user: AdminUser = Depends(require_domain_role("legal", roles=["legal_admin"])),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取管理后台统计"""
    from ..models import Lawyer, Consultation
    from sqlalchemy import select, func, and_

    lawyers_result = await db.execute(select(func.count(Lawyer.id)))
    total_lawyers = lawyers_result.scalar() or 0

    verified_result = await db.execute(
        select(func.count(Lawyer.id)).where(Lawyer.status == "verified")
    )
    verified_lawyers = verified_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Lawyer.id)).where(Lawyer.status == "pending")
    )
    pending_lawyers = pending_result.scalar() or 0

    consultations_result = await db.execute(select(func.count(Consultation.id)))
    total_consultations = consultations_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(Consultation.id)).where(
            Consultation.status.in_(["pending", "processing"])
        )
    )
    active_consultations = active_result.scalar() or 0

    return ApiResponse.success(AdminStatsResponse(
        total_lawyers=total_lawyers,
        verified_lawyers=verified_lawyers,
        pending_lawyers=pending_lawyers,
        total_consultations=total_consultations,
        active_consultations=active_consultations,
    ))


@router.get("/lawyers")
async def list_all_lawyers(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: AdminUser = Depends(require_domain_role("legal", roles=["legal_ops"])),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取所有律师列表"""
    from ..models import Lawyer
    from sqlalchemy import select, func

    query = select(Lawyer)
    if status:
        query = query.where(Lawyer.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Lawyer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    lawyers = result.scalars().all()

    items = [
        {
            "id": l.id,
            "name": l.name,
            "status": l.status,
            "rating": l.rating,
            "consultation_count": l.consultation_count,
            "city": l.city,
        }
        for l in lawyers
    ]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.post("/lawyers/{lawyer_id}/verify")
async def verify_lawyer(
    lawyer_id: int,
    current_user: AdminUser = Depends(require_domain_role("legal", roles=["legal_ops"])),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """认证律师"""
    service = LawyerService(db)
    result = await service.verify(lawyer_id)
    return ApiResponse.success(result)


@router.post("/lawyers/{lawyer_id}/reject")
async def reject_lawyer(
    lawyer_id: int,
    current_user: AdminUser = Depends(require_domain_role("legal", roles=["legal_ops"])),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """拒绝律师"""
    service = LawyerService(db)
    lawyer = await service.get_lawyer(lawyer_id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    lawyer.status = "rejected"
    await db.commit()
    return ApiResponse.success({"id": lawyer_id, "status": "rejected"})


@router.get("/consultations")
async def list_all_consultations(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: AdminUser = Depends(require_domain_role("legal")),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取所有咨询列表"""
    service = ConsultationService(db)

    from ..models import Consultation
    from sqlalchemy import select, func

    query = select(Consultation)
    if status:
        query = query.where(Consultation.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Consultation.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    consultations = result.scalars().all()

    items = [
        {
            "id": c.id,
            "user_id": c.user_id,
            "lawyer_id": c.lawyer_id,
            "category": c.category,
            "title": c.title,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in consultations
    ]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.post("/consultations/{consultation_id}/assign")
async def assign_consultation(
    consultation_id: int,
    lawyer_id: int,
    current_user: AdminUser = Depends(require_domain_role("legal", roles=["lawfirm_owner"])),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """分配咨询给律师"""
    service = ConsultationService(db)
    consultation = await service.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    updated = await service.assign_lawyer(consultation_id, lawyer_id)
    return ApiResponse.success({
        "id": updated.id,
        "lawyer_id": updated.lawyer_id,
        "status": updated.status,
    })


@router.get("/lawyer-consultations")
async def list_appointments(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: AdminUser = Depends(require_domain_role("legal", roles=["lawfirm_owner"])),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取所有预约"""
    service = AppointmentService(db)

    from ..models import LawyerConsultation
    from sqlalchemy import select, func

    query = select(LawyerConsultation)
    if status:
        query = query.where(LawyerConsultation.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(LawyerConsultation.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    appointments = result.scalars().all()

    items = [
        {
            "id": a.id,
            "consultation_id": a.consultation_id,
            "lawyer_id": a.lawyer_id,
            "type": a.type,
            "status": a.status,
            "scheduled_at": a.scheduled_at.isoformat() if a.scheduled_at else None,
        }
        for a in appointments
    ]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)
