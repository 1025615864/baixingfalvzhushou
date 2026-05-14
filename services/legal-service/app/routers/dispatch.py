"""派单路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from ..database import AsyncSessionLocal
from ..models.consultation import Consultation
from ..models.case import DispatchRecord
from ..middleware.auth import get_current_lawyer, AuthUser
from ..schemas.response import ApiResponse

router = APIRouter()


@router.get("/pool")
async def get_dispatch_pool(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取公开抢单池"""
    query = select(Consultation).where(
        and_(Consultation.status == "pending", Consultation.lawyer_id.is_(None))
    )
    if category:
        query = query.where(Consultation.category == category)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    consultations = result.scalars().all()

    count_query = select(func.count(Consultation.id)).where(
        and_(Consultation.status == "pending", Consultation.lawyer_id.is_(None))
    )
    if category:
        count_query = count_query.where(Consultation.category == category)
    total = await db.scalar(count_query)

    items = [
        {
            "id": c.id,
            "user_id": c.user_id,
            "category": c.category,
            "title": c.title,
            "description": c.description,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in consultations
    ]

    return ApiResponse.success({"items": items, "total": total or 0, "page": page, "page_size": page_size})


@router.post("/grab/{consultation_id}")
async def grab_consultation(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """律师抢单"""
    consultation = await db.get(Consultation, consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询不存在")
    if consultation.lawyer_id is not None:
        raise HTTPException(status_code=409, detail="该咨询已被其他律师接单")
    if consultation.status != "pending":
        raise HTTPException(status_code=400, detail="该咨询状态不可抢单")

    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    consultation.lawyer_id = lawyer.id
    consultation.status = "processing"
    await db.commit()

    record = DispatchRecord(
        consultation_id=consultation_id,
        lawyer_id=lawyer.id,
        status="accepted",
    )
    db.add(record)
    await db.commit()

    return ApiResponse.success({"consultation_id": consultation_id, "status": "processing", "message": "抢单成功"})


@router.get("/my-dispatches")
async def get_my_dispatches(
    page: int = 1,
    page_size: int = 20,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取当前律师的派单记录"""
    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    result = await db.execute(
        select(DispatchRecord)
        .where(DispatchRecord.lawyer_id == lawyer.id)
        .order_by(DispatchRecord.dispatched_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = result.scalars().all()

    total = await db.scalar(
        select(func.count(DispatchRecord.id)).where(DispatchRecord.lawyer_id == lawyer.id)
    )

    from sqlalchemy import func
    items = [
        {
            "id": r.id,
            "consultation_id": r.consultation_id,
            "status": r.status,
            "match_score": r.match_score,
            "dispatched_at": r.dispatched_at.isoformat() if r.dispatched_at else None,
            "responded_at": r.responded_at.isoformat() if r.responded_at else None,
        }
        for r in records
    ]

    return ApiResponse.success({"items": items, "total": total or 0, "page": page, "page_size": page_size})