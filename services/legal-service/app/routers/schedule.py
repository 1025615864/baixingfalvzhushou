"""排班路由"""
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.schedule_service import ScheduleService
from ..services.lawyer_service import LawyerService
from ..middleware.auth import get_current_lawyer, AuthUser
from ..schemas.response import ApiResponse

router = APIRouter()


class ScheduleRequest(BaseModel):
    date: str
    start_time: str
    end_time: str


class BulkScheduleRequest(BaseModel):
    schedules: List[ScheduleRequest]


class ScheduleResponse(BaseModel):
    id: int
    lawyer_id: int
    date: str
    start_time: str
    end_time: str
    is_available: bool

    class Config:
        from_attributes = True


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_schedule(
    body: ScheduleRequest,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """创建排班"""
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    try:
        schedule_date = date.fromisoformat(body.date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    service = ScheduleService(db)
    schedule = await service.create(
        lawyer_id=lawyer.id,
        schedule_date=schedule_date,
        start_time=body.start_time,
        end_time=body.end_time,
    )
    return ApiResponse.success([ScheduleResponse.model_validate(schedule)])


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_schedule(
    body: BulkScheduleRequest,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """批量创建排班"""
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    schedules_data = []
    for item in body.schedules:
        try:
            schedule_date = date.fromisoformat(item.date)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {item.date}")
        schedules_data.append({
            "date": schedule_date,
            "start_time": item.start_time,
            "end_time": item.end_time,
        })

    service = ScheduleService(db)
    schedules = await service.bulk_create(lawyer.id, schedules_data)
    return ApiResponse.success([ScheduleResponse.model_validate(s) for s in schedules])


@router.get("/")
async def get_my_schedules(
    year: int,
    month: int,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取当月排班"""
    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    service = ScheduleService(db)
    schedules = await service.get_by_lawyer_month(lawyer.id, year, month)
    return ApiResponse.success([ScheduleResponse.model_validate(s) for s in schedules])


@router.get("/date/{target_date}")
async def get_schedules_by_date(
    target_date: str,
    lawyer_id: Optional[int] = None,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取某天排班 - 公开接口"""
    try:
        schedule_date = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    if lawyer_id:
        service = ScheduleService(db)
        schedules = await service.get_by_lawyer_date(lawyer_id, schedule_date)
    else:
        schedules = []

    return ApiResponse.success([ScheduleResponse.model_validate(s) for s in schedules])


@router.patch("/{schedule_id}/availability")
async def update_schedule_availability(
    schedule_id: int,
    is_available: bool,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """更新排班可用性"""
    service = ScheduleService(db)
    schedule = await service.get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer or lawyer.id != schedule.lawyer_id:
        raise HTTPException(status_code=403, detail="无权操作此排班")

    updated = await service.update_availability(schedule_id, is_available)
    return ApiResponse.success(ScheduleResponse.model_validate(updated))


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """删除排班"""
    service = ScheduleService(db)
    schedule = await service.get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer or lawyer.id != schedule.lawyer_id:
        raise HTTPException(status_code=403, detail="无权操作此排班")

    deleted = await service.delete(schedule_id)
    return ApiResponse.success({"deleted": deleted})


@router.delete("/date/{target_date}")
async def delete_schedules_by_date(
    target_date: str,
    current_user: AuthUser = Depends(get_current_lawyer),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """删除某天所有排班"""
    try:
        schedule_date = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    lawyer_service = LawyerService(db)
    lawyer = await lawyer_service.get_by_user_id(current_user.id)
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    service = ScheduleService(db)
    count = await service.delete_by_lawyer_date(lawyer.id, schedule_date)
    return ApiResponse.success({"deleted": count})
