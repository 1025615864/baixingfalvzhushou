"""
Settlement routers package
"""

from fastapi import APIRouter, Depends, Query
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User
from ...services.settlement_service import settlement_service
from ...utils.deps import get_current_user

from .wallet import router as wallet_router
from .income import router as income_router
from .bank_account import router as bank_account_router
from .withdrawal import router as withdrawal_router
from .admin import router as admin_router

router = APIRouter(prefix="/settlement", tags=["结算服务"])

# 挂载子路由
router.include_router(wallet_router)
router.include_router(income_router)
router.include_router(bank_account_router)
router.include_router(withdrawal_router)
router.include_router(admin_router)


# 兼容前端路由：/settlement/balance（对应 /settlement/wallet）
@router.get("/balance", summary="获取用户余额（兼容路由）")
async def get_balance_compat(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取用户余额，兼容前端 /settlement/balance 接口"""
    wallet = await settlement_service.get_or_create_wallet(db, int(current_user.id))
    return {
        "balance": float(wallet.balance),
        "frozen_balance": float(wallet.frozen_balance),
        "total_withdrawn": float(wallet.total_withdrawn),
        "total_recharged": float(wallet.total_recharged),
    }


# 兼容前端路由：/settlement/records（对应 /settlement/wallet/transactions）
@router.get("/records", summary="获取交易记录（兼容路由）")
async def get_records_compat(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    type_filter: Annotated[str | None, Query(alias="type")] = None,
):
    """获取交易记录，兼容前端 /settlement/records 接口"""
    wallet = await settlement_service.get_or_create_wallet(db, int(current_user.id))
    transactions = await settlement_service.get_transactions(
        db, int(wallet.id), page, page_size, type_filter
    )
    return {
        "items": transactions,
        "total": len(transactions),
        "page": page,
        "page_size": page_size,
    }


# 兼容前端路由：/settlement/withdrawals（对应 /settlement/lawyer/withdrawals）
@router.get("/withdrawals", summary="获取提现记录（兼容路由）")
async def get_withdrawals_compat(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
):
    """获取提现记录，兼容前端 /settlement/withdrawals 接口"""
    from ...models.lawfirm import Lawyer
    from sqlalchemy import select

    res = await db.execute(select(Lawyer).where(Lawyer.user_id == int(current_user.id)))
    lawyer = res.scalar_one_or_none()

    if not lawyer:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    from .withdrawal import _get_withdrawal_list
    return await _get_withdrawal_list(db, lawyer, page, page_size, status_filter)


# Aggregate all settlement routers
__all__ = [
    "router",
    "wallet_router",
    "income_router",
    "bank_account_router",
    "withdrawal_router",
    "admin_router"]
