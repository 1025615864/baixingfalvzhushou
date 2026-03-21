"""余额路由"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.balance_service import BalanceService

router = APIRouter()


class BalanceResponse(BaseModel):
    user_id: int
    balance: float
    total_recharged: float
    total_consumed: float

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    type: str
    amount: float
    balance_before: float
    balance_after: float
    description: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/{user_id}", response_model=BalanceResponse)
async def get_balance(
    user_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取用户余额"""
    service = BalanceService(db)
    balance = await service.get_or_create_balance(user_id)
    return BalanceResponse.model_validate(balance)


@router.get("/{user_id}/transactions")
async def get_transactions(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取余额变动记录"""
    service = BalanceService(db)
    transactions, total = await service.get_transactions(user_id, page, page_size)
    return {
        "items": [TransactionResponse.model_validate(t) for t in transactions],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{user_id}/recharge")
async def recharge_balance(
    user_id: int,
    amount: float,
    order_id: int,
    description: str = "余额充值",
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """充值余额（由支付通道服务调用）"""
    service = BalanceService(db)
    balance = await service.recharge(user_id, amount, order_id, description)
    return BalanceResponse.model_validate(balance)
