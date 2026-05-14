"""咨询路由"""
from typing import Optional
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import Consultation, ChatMessage, ConsultationPayment
from ..services.consultation_service import ConsultationService
from ..middleware.auth import get_current_user, AuthUser
from ..middleware.rate_limit import check_consultation_rate
from ..schemas.response import ApiResponse, PaginatedData

router = APIRouter()


class CreateConsultationRequest(BaseModel):
    category: str
    title: str
    description: str
    ai_assisted: bool = True
    lawyer_id: Optional[int] = None
    consultation_fee: Optional[float] = None


class MessageRequest(BaseModel):
    role: str
    content: str


class UpdateStatusRequest(BaseModel):
    status: str


class ConsultationResponse(BaseModel):
    id: int
    user_id: int
    lawyer_id: Optional[int] = None
    category: str
    title: str
    status: str
    ai_assisted: bool
    payment_order_no: Optional[str] = None
    payment_status: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_consultation(
    request: Request,
    body: CreateConsultationRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """创建咨询 - 需要用户登录"""
    await check_consultation_rate(request)
    service = ConsultationService(db)
    consultation = await service.create(
        user_id=current_user.id,
        category=body.category,
        title=body.title,
        description=body.description,
        ai_assisted=body.ai_assisted,
    )

    payment_order_no = None
    payment_status = None

    if body.lawyer_id and body.consultation_fee and body.consultation_fee > 0:
        await service.assign_lawyer(consultation.id, body.lawyer_id)

        platform_fee = round(body.consultation_fee * 0.15, 2)
        lawyer_income = round(body.consultation_fee - platform_fee, 2)
        order_no = f"CONSULT{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

        payment = ConsultationPayment(
            consultation_id=consultation.id,
            order_no=order_no,
            amount=body.consultation_fee,
            platform_fee=platform_fee,
            lawyer_income=lawyer_income,
            pay_method="wechat",
            status="pending",
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        payment_order_no = payment.order_no
        payment_status = payment.status

        await db.refresh(consultation)

    response = ConsultationResponse.model_validate(consultation)
    response.payment_order_no = payment_order_no
    response.payment_status = payment_status
    return ApiResponse.success(response)


@router.get("/")
async def list_consultations(
    page: int = 1,
    page_size: int = 20,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取当前用户的咨询列表"""
    service = ConsultationService(db)
    consultations, total = await service.list_by_user(current_user.id, page, page_size)
    items = [ConsultationResponse.model_validate(c) for c in consultations]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.get("/{consultation_id}")
async def get_consultation(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取咨询详情"""
    service = ConsultationService(db)
    consultation = await service.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权查看此咨询")
    return ApiResponse.success(ConsultationResponse.model_validate(consultation))


@router.patch("/{consultation_id}/status")
async def update_consultation_status(
    consultation_id: int,
    body: UpdateStatusRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """更新咨询状态"""
    service = ConsultationService(db)
    consultation = await service.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作此咨询")
    updated = await service.update_status(consultation_id, body.status)
    return ApiResponse.success(ConsultationResponse.model_validate(updated))


@router.get("/{consultation_id}/messages")
async def get_messages(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取咨询消息"""
    service = ConsultationService(db)
    consultation = await service.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权查看此咨询")
    messages = await service.get_messages(consultation_id)
    return ApiResponse.success({"items": messages})


@router.post("/{consultation_id}/messages")
async def add_message(
    consultation_id: int,
    request: Request,
    body: MessageRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """添加消息"""
    await check_consultation_rate(request)
    service = ConsultationService(db)
    consultation = await service.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作此咨询")
    message = await service.add_message(
        consultation_id=consultation_id,
        role=body.role,
        content=body.content,
    )
    return ApiResponse.success(message)


@router.post("/{consultation_id}/complete")
async def complete_consultation(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """结束咨询"""
    service = ConsultationService(db)
    consultation = await service.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    from ..services.lawyer_service import LawyerService
    if current_user.role == "lawyer":
        lawyer_service = LawyerService(db)
        lawyer = await lawyer_service.get_by_user_id(current_user.id)
        if not lawyer or lawyer.id != consultation.lawyer_id:
            raise HTTPException(status_code=403, detail="无权操作此咨询")
    elif consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作此咨询")

    completed = await service.complete(consultation_id)
    return ApiResponse.success(ConsultationResponse.model_validate(completed))


@router.post("/{consultation_id}/cancel")
async def cancel_consultation(
    consultation_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """取消咨询"""
    service = ConsultationService(db)
    consultation = await service.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权取消此咨询")

    cancelled = await service.cancel(consultation_id)
    return ApiResponse.success(ConsultationResponse.model_validate(cancelled))


@router.post("/{consultation_id}/assign")
async def assign_lawyer(
    consultation_id: int,
    lawyer_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """分配律师到咨询"""
    service = ConsultationService(db)
    consultation = await service.get(consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    from ..services.lawyer_service import LawyerService
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_lawyer(lawyer_id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    if current_user.role == "lawyer":
        raise HTTPException(status_code=403, detail="普通律师不能分配咨询")

    assigned = await service.assign_lawyer(consultation_id, lawyer_id)

    from ..events.producer import event_bus
    await event_bus.publish_consultation_assigned(consultation, lawyer_id)

    return ApiResponse.success(ConsultationResponse.model_validate(assigned))


@router.get("/pending")
async def list_pending_consultations(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取待分配咨询列表 - 律师可用"""
    service = ConsultationService(db)
    consultations, total = await service.list_pending(page, page_size, category)
    items = [ConsultationResponse.model_validate(c) for c in consultations]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.get("/me/stats")
async def get_my_consultation_stats(
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取我的咨询统计"""
    service = ConsultationService(db)

    if current_user.role == "lawyer":
        from ..services.lawyer_service import LawyerService
        lawyer_service = LawyerService(db)
        lawyer = await lawyer_service.get_by_user_id(current_user.id)
        if not lawyer:
            raise HTTPException(status_code=404, detail="Lawyer not found")
        stats = await service.get_stats(lawyer.id)
    else:
        stats = await service.get_stats()

    return ApiResponse.success(stats)
