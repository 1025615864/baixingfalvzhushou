"""Withdrawal service for settlement."""
from __future__ import annotations
import logging
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _recalc_wallet_fields(wallet):
    pass


class WithdrawalRequestModel:
    def __init__(self, lawyer_id, amount, withdraw_method, bank_account_id=None, status="pending"):
        self.lawyer_id = lawyer_id
        self.amount = amount
        self.withdraw_method = withdraw_method
        self.bank_account_id = bank_account_id
        self.status = status
        self.reject_reason = None
        self.remark = None


class WithdrawalService:
    MIN_WITHDRAWAL = 1.0
    MAX_WITHDRAWAL = 50000.0

    def __init__(self, settlement_service=None):
        self._settlement = settlement_service

    async def create_withdrawal_request(
        self,
        db,
        lawyer_id: int,
        amount: float,
        withdraw_method: str = "bank_card",
        bank_account_id: Optional[int] = None,
    ):
        if amount <= 0:
            raise ValueError("金额不合法")
        if amount > self.MAX_WITHDRAWAL:
            raise ValueError(f"单次最高提现金额为{self.MAX_WITHDRAWAL}元")
        if amount < self.MIN_WITHDRAWAL:
            raise ValueError(f"最低提现金额为{self.MIN_WITHDRAWAL}元")
        wallet = await self._settlement.get_or_create_wallet(db, lawyer_id)
        if wallet.available_amount < amount:
            raise ValueError("可提现余额不足")
        if bank_account_id is not None:
            result = await db.execute(None)
            bank_account = result.scalar_one_or_none() if result else None
            if bank_account is None:
                raise ValueError("收款账户不存在")
        _recalc_wallet_fields(wallet)
        try:
            from app.models.settlement import WithdrawalRequest as WRModel
        except ImportError:
            WRModel = WithdrawalRequestModel
        wr = WRModel(
            lawyer_id=lawyer_id,
            amount=amount,
            withdraw_method=withdraw_method,
            bank_account_id=bank_account_id,
            status="pending",
        )
        db.add(wr)
        await db.commit()
        await db.refresh(wr)
        return wr

    async def admin_set_withdrawal_status(
        self,
        db,
        withdrawal_id: int,
        action: str,
        admin_id: int,
        reject_reason: Optional[str] = None,
        remark: Optional[str] = None,
    ):
        result = await db.execute(None)
        wr = result.scalar_one_or_none() if result else None
        if wr is None:
            raise ValueError("提现申请不存在")
        if action == "approve":
            if wr.status != "pending":
                raise ValueError("仅待审核可通过")
            wr.status = "approved"
            wallet = await self._settlement.get_or_create_wallet(db, wr.lawyer_id)
            wallet.frozen_amount = getattr(wallet, 'frozen_amount', 0) + wr.amount
            wallet.available_amount = getattr(wallet, 'available_amount', 0) - wr.amount
        elif action == "reject":
            wr.status = "rejected"
            if reject_reason:
                wr.reject_reason = reject_reason
        elif action == "complete":
            if wr.status != "approved":
                raise ValueError("仅已审核可完成")
            wr.status = "completed"
            wallet = await self._settlement.get_or_create_wallet(db, wr.lawyer_id)
            wallet.frozen_amount = getattr(wallet, 'frozen_amount', 0) - wr.amount
            wallet.withdrawn_amount = getattr(wallet, 'withdrawn_amount', 0) + wr.amount
        elif action == "fail":
            if wr.status != "approved":
                raise ValueError("仅已审核可标记失败")
            wr.status = "failed"
            wallet = await self._settlement.get_or_create_wallet(db, wr.lawyer_id)
            wallet.frozen_amount = getattr(wallet, 'frozen_amount', 0) - wr.amount
            wallet.available_amount = getattr(wallet, 'available_amount', 0) + wr.amount
            if remark:
                wr.remark = remark
        else:
            raise ValueError("不支持的操作")
        await db.commit()
        await db.refresh(wr)
        return wr
