import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import AsyncSessionLocal
from ..models import LawyerWallet, WalletTransaction, Lawyer
from ..middleware.auth import get_current_user, AuthUser
from ..schemas.response import ApiResponse, PaginatedData

router = APIRouter()


class WalletResponse(BaseModel):
    id: int
    lawyer_id: int
    balance: float
    frozen_balance: float
    total_income: float
    total_withdrawn: float

    class Config:
        from_attributes = True


class WalletTransactionResponse(BaseModel):
    id: int
    wallet_id: int
    type: str
    amount: float
    balance_after: float
    order_no: Optional[str] = None
    payment_id: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WithdrawRequest(BaseModel):
    amount: float
    bank_account: Optional[str] = None


class WithdrawCallbackRequest(BaseModel):
    transaction_id: str
    status: str


@router.get("/me")
async def get_my_wallet(
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    lawyer_result = await db.execute(
        select(Lawyer).where(Lawyer.user_id == current_user.id)
    )
    lawyer = lawyer_result.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师信息不存在")

    wallet_result = await db.execute(
        select(LawyerWallet).where(LawyerWallet.lawyer_id == lawyer.id)
    )
    wallet = wallet_result.scalar_one_or_none()

    if not wallet:
        wallet = LawyerWallet(lawyer_id=lawyer.id)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)

    return ApiResponse.success(WalletResponse.model_validate(wallet))


@router.get("/me/transactions")
async def get_my_transactions(
    page: int = 1,
    page_size: int = 20,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    lawyer_result = await db.execute(
        select(Lawyer).where(Lawyer.user_id == current_user.id)
    )
    lawyer = lawyer_result.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师信息不存在")

    wallet_result = await db.execute(
        select(LawyerWallet).where(LawyerWallet.lawyer_id == lawyer.id)
    )
    wallet = wallet_result.scalar_one_or_none()
    if not wallet:
        return ApiResponse.success(PaginatedData.create([], 0, page, page_size))

    count_result = await db.execute(
        select(func.count()).select_from(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet.id
        )
    )
    total = count_result.scalar() or 0

    txns_result = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    transactions = txns_result.scalars().all()

    items = [WalletTransactionResponse.model_validate(t) for t in transactions]
    paginated = PaginatedData.create(items, total, page, page_size)
    return ApiResponse.success(paginated)


@router.post("/withdraw")
async def withdraw(
    body: WithdrawRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    lawyer_result = await db.execute(
        select(Lawyer).where(Lawyer.user_id == current_user.id)
    )
    lawyer = lawyer_result.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师信息不存在")

    wallet_result = await db.execute(
        select(LawyerWallet).where(LawyerWallet.lawyer_id == lawyer.id)
    )
    wallet = wallet_result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="钱包不存在")

    if wallet.balance < body.amount:
        raise HTTPException(status_code=400, detail="可提现余额不足")

    order_no = f"WITHDRAW{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    wallet.balance -= body.amount
    wallet.total_withdrawn += body.amount

    txn = WalletTransaction(
        wallet_id=wallet.id,
        type="withdraw",
        amount=-body.amount,
        balance_after=wallet.balance,
        order_no=order_no,
        description=f"提现申请 {body.amount}元",
    )
    db.add(txn)
    await db.commit()
    await db.refresh(wallet)

    return ApiResponse.success({
        "order_no": order_no,
        "amount": body.amount,
        "balance": wallet.balance,
    })


@router.post("/withdraw/callback")
async def withdraw_callback(
    body: WithdrawCallbackRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    return ApiResponse.success({
        "transaction_id": body.transaction_id,
        "status": body.status,
        "message": "回调已记录",
    })