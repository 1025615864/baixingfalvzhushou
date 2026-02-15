from __future__ import annotations

from datetime import datetime, timezone
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.calendar import CalendarReminder
from ...models.user import User
from ...schemas.calendar import (
    CalendarReminderCreate,
    CalendarReminderListResponse,
    CalendarReminderResponse,
    CalendarReminderUpdate,
)


async def create_reminder(
    *,
    payload: CalendarReminderCreate,
    current_user: User,
    db: AsyncSession,
) -> CalendarReminderResponse:
    reminder = CalendarReminder(
        user_id=current_user.id,
        title=str(payload.title),
        note=payload.note,
        due_at=payload.due_at,
        remind_at=payload.remind_at,
        is_done=False,
        done_at=None,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return CalendarReminderResponse.model_validate(reminder)


async def list_reminders(
    *,
    current_user: User,
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    done: bool | None = None,
    from_at: datetime | None = None,
    to_at: datetime | None = None,
) -> CalendarReminderListResponse:
    query = select(CalendarReminder).where(
        CalendarReminder.user_id == current_user.id)
    if done is not None:
        query = query.where(CalendarReminder.is_done == bool(done))
    if from_at is not None:
        query = query.where(CalendarReminder.due_at >= from_at)
    if to_at is not None:
        query = query.where(CalendarReminder.due_at <= to_at)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = int(total_result.scalar() or 0)

    query = query.order_by(
        CalendarReminder.due_at.asc(),
        CalendarReminder.id.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(query)
    items = cast(list[CalendarReminder], res.scalars().all())

    return CalendarReminderListResponse(
        items=[CalendarReminderResponse.model_validate(x) for x in items],
        total=total,
    )


async def get_owned_reminder(
    *,
    db: AsyncSession,
    reminder_id: int,
    user_id: int,
) -> CalendarReminder | None:
    res = await db.execute(
        select(CalendarReminder).where(
            CalendarReminder.id == int(reminder_id),
            CalendarReminder.user_id == int(user_id),
        )
    )
    return res.scalar_one_or_none()


async def update_reminder(
    *,
    reminder_id: int,
    payload: CalendarReminderUpdate,
    current_user: User,
    db: AsyncSession,
    _now: datetime | None = None,
) -> CalendarReminderResponse:
    reminder = await get_owned_reminder(
        db=db, reminder_id=reminder_id, user_id=current_user.id
    )
    if reminder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在")

    if payload.title is not None:
        reminder.title = payload.title
    if payload.note is not None:
        reminder.note = payload.note
    if payload.due_at is not None:
        reminder.due_at = payload.due_at
    if payload.remind_at is not None:
        reminder.remind_at = payload.remind_at

    if payload.is_done is not None:
        next_done = bool(payload.is_done)
        reminder.is_done = next_done
        if next_done:
            if reminder.done_at is None:
                now = _now if _now is not None else datetime.now(timezone.utc)
                reminder.done_at = now
        else:
            reminder.done_at = None

    await db.commit()
    await db.refresh(reminder)
    return CalendarReminderResponse.model_validate(reminder)


async def delete_reminder(
    *,
    reminder_id: int,
    current_user: User,
    db: AsyncSession,
) -> dict[str, str]:
    reminder = await get_owned_reminder(
        db=db, reminder_id=reminder_id, user_id=current_user.id
    )
    if reminder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在")

    await db.delete(reminder)
    await db.commit()
    return {"message": "删除成功"}
