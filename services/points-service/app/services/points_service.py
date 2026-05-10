from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from fastapi import HTTPException

from ..models import PointsUser, PointsHistory, PointsMallItem, PointsExchangeOrder, DailyCheckIn


async def _get_or_create_user(session: AsyncSession, user_id: int) -> PointsUser:
    result = await session.execute(
        select(PointsUser).where(PointsUser.user_id == user_id)
    )
    points_user = result.scalar_one_or_none()
    if not points_user:
        points_user = PointsUser(user_id=user_id, balance=0, total_earned=0, total_spent=0)
        session.add(points_user)
        await session.flush()
    return points_user


async def _calculate_streak(session: AsyncSession, user_id: int, today: date) -> int:
    result = await session.execute(
        select(DailyCheckIn.check_in_date)
        .where(DailyCheckIn.user_id == user_id)
        .order_by(DailyCheckIn.check_in_date.desc())
        .limit(30)
    )
    dates = set(row[0] for row in result.all())
    if not dates:
        return 0
    streak = 0
    check_date = today
    if today.isoformat() not in dates:
        check_date = today - timedelta(days=1)
    for _ in range(30):
        if check_date.isoformat() in dates:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak


async def add_points(
    session: AsyncSession, user_id: int, points: int, source: str, description: str
) -> PointsHistory:
    points_user = await _get_or_create_user(session, user_id)
    new_balance = points_user.balance + points
    history = PointsHistory(
        user_id=user_id,
        change=points,
        balance_after=new_balance,
        source=source,
        description=description,
    )
    session.add(history)
    points_user.balance = new_balance
    points_user.total_earned += points
    await session.flush()
    await session.refresh(history)
    return history


async def deduct_points(
    session: AsyncSession, user_id: int, points: int, source: str, description: str
) -> PointsHistory:
    points_user = await _get_or_create_user(session, user_id)
    new_balance = points_user.balance - points
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Insufficient points")
    history = PointsHistory(
        user_id=user_id,
        change=-points,
        balance_after=new_balance,
        source=source,
        description=description,
    )
    session.add(history)
    points_user.balance = new_balance
    points_user.total_spent += points
    await session.flush()
    await session.refresh(history)
    return history


async def get_points_history(
    session: AsyncSession,
    user_id: int,
    source: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    query = select(PointsHistory).where(PointsHistory.user_id == user_id)
    if source:
        query = query.where(PointsHistory.source == source)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    query = query.order_by(desc(PointsHistory.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    items = result.scalars().all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def daily_check_in(session: AsyncSession, user_id: int) -> dict:
    today = date.today()
    today_str = today.isoformat()
    result = await session.execute(
        select(DailyCheckIn).where(
            DailyCheckIn.user_id == user_id,
            DailyCheckIn.check_in_date == today_str,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Already checked in today")
    previous_streak = await _calculate_streak(session, user_id, today)
    points_awarded = 10 + min(previous_streak, 7) * 5
    check_in_record = DailyCheckIn(
        user_id=user_id,
        check_in_date=today_str,
        points_awarded=points_awarded,
    )
    session.add(check_in_record)
    await add_points(
        session, user_id, points_awarded, "check_in",
        f"Daily check-in, streak {previous_streak + 1}"
    )
    await session.flush()
    new_streak = previous_streak + 1
    return {
        "checked_in": True,
        "points_awarded": points_awarded,
        "current_streak": new_streak,
    }


async def get_check_in_status(session: AsyncSession, user_id: int) -> dict:
    today = date.today()
    today_str = today.isoformat()
    result = await session.execute(
        select(DailyCheckIn).where(
            DailyCheckIn.user_id == user_id,
            DailyCheckIn.check_in_date == today_str,
        )
    )
    today_check_in = result.scalar_one_or_none()
    streak = await _calculate_streak(session, user_id, today)
    return {
        "user_id": user_id,
        "checked_in_today": today_check_in is not None,
        "current_streak": streak,
        "today_points": today_check_in.points_awarded if today_check_in else None,
    }


async def list_mall_items(
    session: AsyncSession, page: int = 1, page_size: int = 20
) -> dict:
    query = select(PointsMallItem).where(PointsMallItem.status == "active")
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    query = query.order_by(desc(PointsMallItem.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    items = result.scalars().all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def exchange_item(
    session: AsyncSession, user_id: int, item_id: int
) -> PointsExchangeOrder:
    result = await session.execute(
        select(PointsMallItem).where(PointsMallItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.status != "active":
        raise HTTPException(status_code=400, detail="Item is not available")
    if item.stock <= 0:
        raise HTTPException(status_code=400, detail="Item out of stock")
    points_user = await _get_or_create_user(session, user_id)
    if points_user.balance < item.points_cost:
        raise HTTPException(status_code=400, detail="Insufficient points")
    new_balance = points_user.balance - item.points_cost
    history = PointsHistory(
        user_id=user_id,
        change=-item.points_cost,
        balance_after=new_balance,
        source="exchange",
        description=f"Exchange for {item.name}",
    )
    session.add(history)
    points_user.balance = new_balance
    points_user.total_spent += item.points_cost
    item.stock -= 1
    order = PointsExchangeOrder(
        user_id=user_id,
        item_id=item_id,
        points_cost=item.points_cost,
        status="completed",
    )
    session.add(order)
    await session.flush()
    await session.refresh(order)
    return order


async def get_exchange_orders(
    session: AsyncSession, user_id: int, page: int = 1, page_size: int = 20
) -> dict:
    query = select(PointsExchangeOrder).where(
        PointsExchangeOrder.user_id == user_id
    )
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    query = query.order_by(desc(PointsExchangeOrder.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    items = result.scalars().all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}
