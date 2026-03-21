"""积分路由"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..database import get_db
from ..models import PointsUser, PointsHistory

router = APIRouter()


class PointsResponse(BaseModel):
    user_id: int
    balance: int
    total_earned: int
    total_spent: int

    class Config:
        from_attributes = True


class PointsHistoryItem(BaseModel):
    id: int
    change: int
    balance_after: int
    source: str
    description: str | None
    created_at: str

    class Config:
        from_attributes = True


class PointsHistoryResponse(BaseModel):
    items: List[PointsHistoryItem]
    total: int
    page: int
    page_size: int


class PointsChangeRequest(BaseModel):
    change: int
    source: str
    description: str | None = None
    reference_id: str | None = None


@router.get("/{user_id}", response_model=PointsResponse)
async def get_balance(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户积分余额"""
    result = await db.execute(
        select(PointsUser).where(PointsUser.user_id == user_id)
    )
    points_user = result.scalar_one_or_none()
    
    if not points_user:
        points_user = PointsUser(user_id=user_id, balance=0, total_earned=0, total_spent=0)
        db.add(points_user)
        await db.commit()
        await db.refresh(points_user)
    
    return PointsResponse(
        user_id=points_user.user_id,
        balance=points_user.balance,
        total_earned=points_user.total_earned,
        total_spent=points_user.total_spent
    )


@router.get("/{user_id}/history", response_model=PointsHistoryResponse)
async def get_history(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取用户积分变动历史"""
    query = select(PointsHistory).where(PointsHistory.user_id == user_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(desc(PointsHistory.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    items = [
        PointsHistoryItem(
            id=h.id,
            change=h.change,
            balance_after=h.balance_after,
            source=h.source,
            description=h.description,
            created_at=h.created_at.isoformat() if h.created_at else ""
        )
        for h in history
    ]
    
    return PointsHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/{user_id}/change")
async def change_points(
    user_id: int,
    request: PointsChangeRequest,
    db: AsyncSession = Depends(get_db)
):
    """修改用户积分（增加或减少）"""
    result = await db.execute(
        select(PointsUser).where(PointsUser.user_id == user_id)
    )
    points_user = result.scalar_one_or_none()
    
    if not points_user:
        points_user = PointsUser(user_id=user_id, balance=0, total_earned=0, total_spent=0)
        db.add(points_user)
        await db.flush()
    
    new_balance = points_user.balance + request.change
    
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Insufficient points")
    
    history = PointsHistory(
        user_id=user_id,
        change=request.change,
        balance_after=new_balance,
        source=request.source,
        description=request.description,
        reference_id=request.reference_id
    )
    db.add(history)
    
    points_user.balance = new_balance
    if request.change > 0:
        points_user.total_earned += request.change
    else:
        points_user.total_spent += abs(request.change)
    
    await db.commit()
    
    return {
        "success": True,
        "balance": new_balance,
        "change": request.change
    }
