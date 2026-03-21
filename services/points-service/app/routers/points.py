"""积分路由"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import AsyncSessionLocal

router = APIRouter()


class PointsResponse(BaseModel):
    user_id: int
    balance: int

    class Config:
        from_attributes = True


@router.get("/{user_id}", response_model=PointsResponse)
async def get_balance(user_id: int):
    return PointsResponse(user_id=user_id, balance=0)


@router.get("/{user_id}/history")
async def get_history(user_id: int, page: int = 1, page_size: int = 20):
    return {"items": [], "total": 0}
