"""咨询领域路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...schemas import (
    ConsultationResponse,
    ConsultationCreate,
    MessageResponse,
    MessageCreate,
)
from ...services import ConsultationService
from ...middleware.auth import require_permissions
from ...shared.permissions import Permission

router = APIRouter(prefix="/consultations", tags=["咨询"])


@router.post("/", response_model=ConsultationResponse)
async def create_consultation(
    request: ConsultationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.CONSULTATION_CREATE)),
):
    service = ConsultationService(db)
    consultation = await service.create(
        user_id=current_user.id,
        category=request.category,
        title=request.title,
        description=request.description,
        ai_assisted=request.ai_assisted,
    )
    return ConsultationResponse.model_validate(consultation)


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.CONSULTATION_READ)),
):
    service = ConsultationService(db)
    consultation = await service.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询不存在")
    return ConsultationResponse.model_validate(consultation)


@router.get("/user/me")
async def get_my_consultations(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.CONSULTATION_READ)),
):
    service = ConsultationService(db)
    consultations, total = await service.list_by_user(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [ConsultationResponse.model_validate(c) for c in consultations],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{consultation_id}/messages")
async def get_consultation_messages(
    consultation_id: int,
    cursor: int = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.CONSULTATION_READ)),
):
    service = ConsultationService(db)
    messages = await service.get_messages(
        consultation_id=consultation_id,
        cursor=cursor,
        limit=limit,
    )
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/{consultation_id}/messages")
async def create_message(
    consultation_id: int,
    request: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.CONSULTATION_CREATE)),
):
    service = ConsultationService(db)
    message = await service.add_message(
        consultation_id=consultation_id,
        role=request.role,
        content=request.content,
    )
    return MessageResponse.model_validate(message)