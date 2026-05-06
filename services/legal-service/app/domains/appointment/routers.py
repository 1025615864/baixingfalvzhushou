"""预约领域路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...schemas import AppointmentResponse
from ...services import AppointmentService
from ...middleware.auth import require_permissions
from ...shared.permissions import Permission

router = APIRouter(prefix="/appointments", tags=["预约"])


@router.post("/")
async def create_appointment(
    consultation_id: int,
    lawyer_id: int,
    appointment_type: str,
    scheduled_at: str,
    price: float = 0.0,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.APPOINTMENT_CREATE)),
):
    from datetime import datetime
    service = AppointmentService(db)
    appointment = await service.create(
        consultation_id=consultation_id,
        lawyer_id=lawyer_id,
        appointment_type=appointment_type,
        scheduled_at=datetime.fromisoformat(scheduled_at),
        price=price,
    )
    return AppointmentResponse.model_validate(appointment)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.APPOINTMENT_READ)),
):
    service = AppointmentService(db)
    appointment = await service.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    return AppointmentResponse.model_validate(appointment)


@router.patch("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.APPOINTMENT_CANCEL)),
):
    service = AppointmentService(db)
    appointment = await service.cancel(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    return {"message": "预约已取消"}


@router.patch("/{appointment_id}/accept")
async def accept_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.APPOINTMENT_MANAGE)),
):
    service = AppointmentService(db)
    appointment = await service.accept(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="预约不存在")
    return {"message": "预约已确认"}


@router.get("/lawyer/{lawyer_id}")
async def list_lawyer_appointments(
    lawyer_id: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permissions(Permission.APPOINTMENT_READ)),
):
    service = AppointmentService(db)
    appointments, total = await service.list_by_lawyer(
        lawyer_id=lawyer_id,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [AppointmentResponse.model_validate(a) for a in appointments],
        "total": total,
        "page": page,
        "page_size": page_size,
    }