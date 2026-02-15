"""日程管理路由"""

from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db

from ...models.user import User
from ...schemas.lawfirm import (
    LawyerScheduleCreate,
    LawyerScheduleUpdate,
    LawyerScheduleResponse,
    LawyerScheduleListResponse,
    AvailableSlotsResponse,
    AvailableSlotResponse,
)
from ...services.lawfirm_service import schedule_service
from ...utils.deps import get_current_user

router = APIRouter(prefix="/lawyer/schedules", tags=["日程管理"])


async def _require_verified_lawyer(db: AsyncSession, current_user: User):
    """获取当前用户的律师信息"""
    from ...models.lawfirm import Lawyer
    from sqlalchemy import select

    role = str(getattr(current_user, "role", "") or "").lower()
    if role in {"admin", "super_admin"}:
        raise HTTPException(status_code=403, detail="管理员不支持使用律师工作台")

    if role == "lawyer":
        res = await db.execute(
            select(Lawyer).where(
                Lawyer.user_id == int(current_user.id),
                Lawyer.is_active,
            )
        )
        lawyer = res.scalar_one_or_none()
        if not lawyer:
            raise HTTPException(status_code=403, detail="未绑定律师资料")
        return lawyer

    res = await db.execute(
        select(Lawyer).where(
            Lawyer.user_id == int(current_user.id),
            Lawyer.is_active,
        )
    )
    lawyer = res.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(status_code=403, detail="未绑定律师资料")
    return lawyer


@router.get("", response_model=LawyerScheduleListResponse, summary="律师-获取我的日程")
async def lawyer_get_my_schedules(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    """律师获取自己的日程列表"""
    lawyer = await _require_verified_lawyer(db, current_user)

    # 使用服务层获取日程列表
    schedules, total = await schedule_service.get_by_lawyer_id(
        db, lawyer.id, page, page_size, date_from, date_to
    )

    items = []
    for s in schedules:
        items.append(LawyerScheduleResponse(
            id=s.id,
            lawyer_id=s.lawyer_id,
            date=s.date,
            start_time=s.start_time,
            end_time=s.end_time,
            is_available=s.is_available,
            consultation_id=s.consultation_id,
            note=s.note,
            created_at=s.created_at,
            updated_at=s.updated_at,
        ))

    return LawyerScheduleListResponse(
        items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=LawyerScheduleResponse, summary="律师-创建日程")
async def lawyer_create_schedule(
    data: LawyerScheduleCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师创建日程"""
    lawyer = await _require_verified_lawyer(db, current_user)

    # 验证时间格式和逻辑
    if data.start_time >= data.end_time:
        raise HTTPException(status_code=400, detail="开始时间必须早于结束时间")

    # 使用服务层创建日程
    schedule = await schedule_service.create(db, lawyer.id, data)

    return LawyerScheduleResponse(
        id=schedule.id,
        lawyer_id=schedule.lawyer_id,
        date=schedule.date,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        is_available=schedule.is_available,
        consultation_id=schedule.consultation_id,
        note=schedule.note,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.put("/{schedule_id}",
            response_model=LawyerScheduleResponse, summary="律师-更新日程")
async def lawyer_update_schedule(
    schedule_id: int,
    data: LawyerScheduleUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师更新日程"""
    lawyer = await _require_verified_lawyer(db, current_user)

    # 使用服务层更新日程
    schedule = await schedule_service.update(db, schedule_id, data)
    if not schedule:
        raise HTTPException(status_code=404, detail="日程不存在")

    return LawyerScheduleResponse(
        id=schedule.id,
        lawyer_id=schedule.lawyer_id,
        date=schedule.date,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        is_available=schedule.is_available,
        consultation_id=schedule.consultation_id,
        note=schedule.note,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.delete("/{schedule_id}", summary="律师-删除日程")
async def lawyer_delete_schedule(
    schedule_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """律师删除日程"""
    lawyer = await _require_verified_lawyer(db, current_user)

    # 使用服务层删除日程
    success = await schedule_service.delete(db, schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="日程不存在")

    return {"detail": "日程已删除"}


@router.get("/lawyers/{lawyer_id}/available-slots",
            response_model=AvailableSlotsResponse, summary="查询律师可用时段")
async def get_lawyer_available_slots(
    lawyer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    date: datetime,
):
    """查询律师在指定日期的可用时段"""
    # 使用服务层获取可用时间段
    slots = await schedule_service.get_available_slots(db, lawyer_id, date)

    slot_responses = []
    for slot in slots:
        slot_responses.append(AvailableSlotResponse(
            date=date,
            start_time=slot['start_time'],
            end_time=slot['end_time'],
        ))

    return {"lawyer_id": lawyer_id, "date": date, "slots": slot_responses}
