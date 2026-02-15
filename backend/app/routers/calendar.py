from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..schemas.calendar import (
    CalendarReminderCreate,
    CalendarReminderListResponse,
    CalendarReminderResponse,
    CalendarReminderUpdate,
)
from ..services.calendar import (
    create_reminder as create_reminder_service,
    delete_reminder as delete_reminder_service,
    list_reminders as list_reminders_service,
    update_reminder as update_reminder_service,
)
from ..utils.deps import get_current_user

router = APIRouter(prefix="/calendar", tags=["法律日历"])


@router.post("/reminders", response_model=CalendarReminderResponse)
async def create_reminder(
    payload: CalendarReminderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await create_reminder_service(
        payload=payload,
        current_user=current_user,
        db=db,
    )


@router.get("/reminders", response_model=CalendarReminderListResponse)
async def list_reminders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    done: bool | None = None,
    from_at: datetime | None = None,
    to_at: datetime | None = None,
):
    return await list_reminders_service(
        current_user=current_user,
        db=db,
        page=page,
        page_size=page_size,
        done=done,
        from_at=from_at,
        to_at=to_at,
    )


@router.put("/reminders/{reminder_id}",
            response_model=CalendarReminderResponse)
async def update_reminder(
    reminder_id: int,
    payload: CalendarReminderUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _now: datetime | None = None,
):
    return await update_reminder_service(
        reminder_id=reminder_id,
        payload=payload,
        current_user=current_user,
        db=db,
        _now=_now,
    )


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await delete_reminder_service(
        reminder_id=reminder_id,
        current_user=current_user,
        db=db,
    )
