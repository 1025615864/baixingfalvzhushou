"""用户举报路由"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel

from ..database import get_db
from ..models import Report
from ..middleware import AuthMiddleware, AuthUser
from ..clients import user_service_client

router = APIRouter()

auth_middleware = AuthMiddleware(user_client=user_service_client)


class ReportCreateRequest(BaseModel):
    target_type: str
    target_id: int
    reason: str
    detail: Optional[str] = None


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    target_type: str
    target_id: int
    reason: str
    detail: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    current_user = await auth_middleware.get_current_user(request)

    if report_data.target_type not in ["post", "comment"]:
        raise HTTPException(status_code=400, detail="无效的举报类型")

    if len(report_data.reason) < 5:
        raise HTTPException(status_code=400, detail="举报原因至少5个字符")

    existing = await db.execute(
        select(Report).where(
            and_(
                Report.reporter_id == current_user.id,
                Report.target_type == report_data.target_type,
                Report.target_id == report_data.target_id,
                Report.status == "pending"
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="您已举报过此内容")

    report = Report(
        reporter_id=current_user.id,
        target_type=report_data.target_type,
        target_id=report_data.target_id,
        reason=report_data.reason,
        detail=report_data.detail,
        status="pending"
    )

    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportResponse.model_validate(report)


@router.get("/my")
async def get_my_reports(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    current_user = await auth_middleware.get_current_user(request)

    query = select(Report).where(Report.reporter_id == current_user.id)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = query.order_by(desc(Report.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    reports = result.scalars().all()

    return {
        "items": [ReportResponse.model_validate(r) for r in reports],
        "total": total,
        "page": page,
        "page_size": page_size
    }
