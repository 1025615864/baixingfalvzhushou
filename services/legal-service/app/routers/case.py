"""案件管理路由"""
import uuid
from typing import Optional
from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import AsyncSessionLocal
from ..models.case import LawCase
from ..middleware.auth import get_current_user, get_current_lawyer, AuthUser
from ..schemas.response import ApiResponse, PaginatedData

router = APIRouter()


class CreateCaseRequest(BaseModel):
    consultation_id: Optional[int] = None
    title: str
    client_name: Optional[str] = None
    category: str
    priority: int = 0
    source: str = "platform"


class UpdateCaseRequest(BaseModel):
    title: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None


class ProgressNodeRequest(BaseModel):
    title: str
    description: str


class CloseCaseRequest(BaseModel):
    result_type: str
    result_report: Optional[str] = None


@router.get("/")
async def list_my_cases(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律师案件列表"""
    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    query = select(LawCase).where(LawCase.lawyer_id == lawyer.id)
    if status:
        query = query.where(LawCase.status == status)
    query = query.order_by(LawCase.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    cases = result.scalars().all()

    count_query = select(func.count(LawCase.id)).where(LawCase.lawyer_id == lawyer.id)
    if status:
        count_query = count_query.where(LawCase.status == status)
    total = await db.scalar(count_query)

    items = [
        {
            "id": c.id,
            "case_no": c.case_no,
            "consultation_id": c.consultation_id,
            "title": c.title,
            "client_name": c.client_name,
            "category": c.category,
            "status": c.status,
            "priority": c.priority,
            "source": c.source,
            "result_type": c.result_type,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in cases
    ]

    return ApiResponse.success({"items": items, "total": total or 0, "page": page, "page_size": page_size})


@router.post("/")
async def create_case(
    body: CreateCaseRequest,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """创建案件"""
    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    case_no = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    case = LawCase(
        case_no=case_no,
        consultation_id=body.consultation_id,
        lawyer_id=lawyer.id,
        user_id=None,
        title=body.title,
        client_name=body.client_name,
        category=body.category,
        priority=body.priority,
        source=body.source,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)

    return ApiResponse.success({
        "id": case.id,
        "case_no": case.case_no,
        "title": case.title,
        "status": case.status,
        "created_at": case.created_at.isoformat() if case.created_at else None,
    })


@router.get("/{case_id}")
async def get_case(
    case_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取案件详情"""
    case = await db.get(LawCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    progress = json.loads(case.progress_nodes) if case.progress_nodes else []

    return ApiResponse.success({
        "id": case.id,
        "case_no": case.case_no,
        "consultation_id": case.consultation_id,
        "lawyer_id": case.lawyer_id,
        "user_id": case.user_id,
        "title": case.title,
        "client_name": case.client_name,
        "category": case.category,
        "status": case.status,
        "priority": case.priority,
        "progress_nodes": progress,
        "result_type": case.result_type,
        "result_report": case.result_report,
        "source": case.source,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
        "archived_at": case.archived_at.isoformat() if case.archived_at else None,
    })


@router.patch("/{case_id}")
async def update_case(
    case_id: int,
    body: UpdateCaseRequest,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """更新案件"""
    case = await db.get(LawCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    if body.title is not None:
        case.title = body.title
    if body.client_name is not None:
        case.client_name = body.client_name
    if body.status is not None:
        case.status = body.status
    if body.priority is not None:
        case.priority = body.priority

    case.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(case)

    return ApiResponse.success({"id": case.id, "status": case.status, "updated_at": case.updated_at.isoformat()})


@router.post("/{case_id}/progress")
async def add_progress_node(
    case_id: int,
    body: ProgressNodeRequest,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """添加案件进度节点"""
    case = await db.get(LawCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    nodes = json.loads(case.progress_nodes) if case.progress_nodes else []
    nodes.append({
        "date": datetime.now().isoformat(),
        "title": body.title,
        "description": body.description,
    })

    case.progress_nodes = json.dumps(nodes, ensure_ascii=False)
    case.updated_at = datetime.utcnow()
    await db.commit()

    return ApiResponse.success({"case_id": case_id, "progress_nodes": nodes, "count": len(nodes)})


@router.post("/{case_id}/close")
async def close_case(
    case_id: int,
    body: CloseCaseRequest,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """结案归档"""
    case = await db.get(LawCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")

    case.status = "closed"
    case.result_type = body.result_type
    case.result_report = body.result_report
    case.archived_at = datetime.utcnow()
    case.updated_at = datetime.utcnow()
    await db.commit()

    return ApiResponse.success({
        "id": case.id,
        "case_no": case.case_no,
        "status": "closed",
        "result_type": case.result_type,
        "archived_at": case.archived_at.isoformat(),
    })


@router.get("/stats/summary")
async def get_case_stats(
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """案件统计概览"""
    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")

    active_count = await db.scalar(
        select(func.count(LawCase.id)).where(
            LawCase.lawyer_id == lawyer.id, LawCase.status == "active"
        )
    )
    closed_count = await db.scalar(
        select(func.count(LawCase.id)).where(
            LawCase.lawyer_id == lawyer.id, LawCase.status.in_(["closed", "archived"])
        )
    )
    win_count = await db.scalar(
        select(func.count(LawCase.id)).where(
            LawCase.lawyer_id == lawyer.id, LawCase.result_type == "win"
        )
    )
    win_rate = round(win_count / closed_count * 100, 1) if closed_count and closed_count > 0 else 0

    channel_result = await db.execute(
        select(LawCase.source, func.count(LawCase.id))
        .where(LawCase.lawyer_id == lawyer.id)
        .group_by(LawCase.source)
    )
    channels = [{"channel": r[0] or "other", "count": r[1]} for r in channel_result.all()]

    return ApiResponse.success({
        "active_count": active_count or 0,
        "closed_count": closed_count or 0,
        "win_rate": win_rate,
        "win_count": win_count or 0,
        "channel_distribution": channels,
    })