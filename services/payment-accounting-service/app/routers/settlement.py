"""结算路由"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.settlement_service import SettlementService

router = APIRouter()


class WalletResponse(BaseModel):
    lawyer_id: int
    balance: float
    total_income: float
    total_withdrawn: float

    class Config:
        from_attributes = True


@router.get("/wallet/{lawyer_id}", response_model=WalletResponse)
async def get_wallet(
    lawyer_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取律师钱包"""
    service = SettlementService(db)
    wallet = await service.get_or_create_wallet(lawyer_id)
    return WalletResponse.model_validate(wallet)


@router.post("/withdraw")
async def withdraw(
    lawyer_id: int,
    amount: float,
    bank_account: str,
    real_name: str,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """申请提现"""
    service = SettlementService(db)
    result = await service.withdraw(lawyer_id, amount, bank_account, real_name)
    return result
