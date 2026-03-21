"""咨询路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import Consultation, ChatMessage
from ..services.consultation_service import ConsultationService

router = APIRouter()


class CreateConsultationRequest(BaseModel):
    user_id: int
    category: str
    title: str
    description: str
    ai_assisted: bool = True


class MessageRequest(BaseModel):
    role: str
    content: str


class ConsultationResponse(BaseModel):
    id: int
    user_id: int
    lawyer_id: Optional[int] = None
    category: str
    title: str
    status: str
    ai_assisted: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=ConsultationResponse)
async def create_consultation(
    request: CreateConsultationRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """创建咨询"""
    service = ConsultationService(db)
    consultation = await service.create(
        user_id=request.user_id,
        category=request.category,
        title=request.title,
        description=request.description,
        ai_assisted=request.ai_assisted,
    )
    return ConsultationResponse.model_validate(consultation)


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取咨询详情"""
    service = ConsultationService(db)
    consultation = await service.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return ConsultationResponse.model_validate(consultation)


@router.get("/{consultation_id}/messages")
async def get_messages(
    consultation_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取咨询消息"""
    service = ConsultationService(db)
    messages = await service.get_messages(consultation_id)
    return {"items": messages}


@router.post("/{consultation_id}/messages")
async def add_message(
    consultation_id: int,
    request: MessageRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """添加消息"""
    service = ConsultationService(db)
    message = await service.add_message(
        consultation_id=consultation_id,
        role=request.role,
        content=request.content,
    )
    return message
