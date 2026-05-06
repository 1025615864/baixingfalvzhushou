"""预约路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..database import AsyncSessionLocal
from ..services.appointment_service import AppointmentService
from ..services.consultation_service import ConsultationService
from ..services.lawyer_service import LawyerService
from ..middleware.auth import get_current_user, get_current_lawyer, AuthUser
from ..middleware.rate_limit import check_consultation_rate
from ..schemas.response import ApiResponse, PaginatedData

router = APIRouter()


class CreateAppointmentRequest(BaseModel):
    consultation_id: int
    lawyer_id: int
    appointment_type: str
    scheduled_at: str
    price: float = 0.0


class AppointmentResponse(BaseModel):
    id: int
    consultation_id: int
    lawyer_id: int
    type: str
    status: str
    scheduled_at: Optional[str] = None
    price: float
    created_at: str

    class Config:
        from_attributes = True


class AvailableSlotResponse(BaseModel):
    start_time: str
    end_time: str
    is_available: bool


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    request: Request,
    body: CreateAppointmentRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """创建预约 - 需要用户登录"""
    consultation_service = ConsultationService(db)
    consultation = await consultation_service.get(body.consultation_id)

    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权操作此咨询")

    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_lawyer(body.lawyer_id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    service = AppointmentService(db)

    try:
        scheduled_dt = datetime.fromisoformat(body.scheduled_at.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")

    if await service.check_time_conflict(body.lawyer_id, scheduled_dt):
        raise HTTPException(status_code=409, detail="预约时间冲突")

    appointment = await service.create(
        consultation_id=body.consultation_id,
        lawyer_id=body.lawyer_id,
        appointment_type=body.appointment_type,
        scheduled_at=scheduled_dt,
        price=body.price,
    )
    return ApiResponse.success(AppointmentResponse.model_validate(appointment))


@router.get("/")
async def list_my_appointments(
    page: int = 1,
    page_size: int = 20,
    as_role: str = "user",
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取我的预约列表"""
    service = AppointmentService(db)

    if as_role == "lawyer" and current_user.role in ["lawyer", "admin"]:
        lawyer_service = LawyerService(db)
        lawyer = await lawyer_service.get_by_user_id(current_user.id)
        if not lawyer:
            raise HTTPException(status_code=404, detail="Lawyer not found")
        appointments, total = await service.list_by_lawyer(lawyer.id, page, page_size)
    else:
        appointments, total = await service.list_by_user(current_user.id, page, page_size)

    items = [AppointmentResponse.model_validate(a) for a in appointments]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取预约详情"""
    service = AppointmentService(db)
    appointment = await service.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return ApiResponse.success(AppointmentResponse.model_validate(appointment))


@router.patch("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: int,
    new_status: str,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """更新预约状态"""
    service = AppointmentService(db)
    appointment = await service.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    from ..services.consultation_service import ConsultationService
    consultation_service = ConsultationService(db)
    consultation = await consultation_service.get(appointment.consultation_id)

    if consultation.user_id != current_user.id and current_user.role != "admin":
        if current_user.role == "lawyer":
            lawyer_service = LawyerService(db)
            lawyer = await lawyer_service.get_by_user_id(current_user.id)
            if not lawyer or lawyer.id != appointment.lawyer_id:
                raise HTTPException(status_code=403, detail="无权操作此预约")

    updated = await service.update_status(appointment_id, new_status)
    return ApiResponse.success(AppointmentResponse.model_validate(updated))


@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: int,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """取消预约"""
    service = AppointmentService(db)
    appointment = await service.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    from ..services.consultation_service import ConsultationService
    consultation_service = ConsultationService(db)
    consultation = await consultation_service.get(appointment.consultation_id)

    if consultation.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权取消此预约")

    cancelled = await service.cancel(appointment_id)
    return ApiResponse.success(AppointmentResponse.model_validate(cancelled))


@router.get("/lawyer/{lawyer_id}/available-slots")
async def get_available_slots(
    lawyer_id: int,
    date: str,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律师可用时段"""
    try:
        target_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    service = AppointmentService(db)
    slots = await service.get_available_slots(lawyer_id, target_date)
    items = [AvailableSlotResponse.model_validate(s) for s in slots]
    return ApiResponse.success({"items": items, "total": len(slots)})
