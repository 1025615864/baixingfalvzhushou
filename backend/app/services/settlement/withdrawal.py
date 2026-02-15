"""提现服务模块

包含：
- WithdrawalService: 提现申请和管理
"""
from __future__ import annotations

import json
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.lawfirm import Lawyer
from ...models.notification import Notification, NotificationType
from ...models.settlement import LawyerBankAccount, LawyerIncomeRecord, WithdrawalRequest

from .core import (
    SettlementService,
    SETTLEMENT_WITHDRAW_FEE,
    SETTLEMENT_WITHDRAW_MAX_AMOUNT,
    SETTLEMENT_WITHDRAW_MIN_AMOUNT,
    _mask_account_no,
    _now,
    _quantize_amount,
    _decimal_to_cents,
    _recalc_wallet_fields,
)


class WithdrawalService:
    """提现服务"""

    def __init__(self, settlement_service: SettlementService):
        self._settlement = settlement_service

    async def create_withdrawal_request(
        self,
        db: AsyncSession,
        *,
        lawyer_id: int,
        amount: float,
        withdraw_method: str,
        bank_account_id: int,
    ) -> WithdrawalRequest:
        """创建提现申请"""
        wallet = await self._settlement.get_or_create_wallet(db, int(lawyer_id))
        _recalc_wallet_fields(wallet)

        amt = _quantize_amount(float(amount))
        if amt <= Decimal("0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="金额不合法")

        if float(amt) > float(SETTLEMENT_WITHDRAW_MAX_AMOUNT):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"单次最高提现金额为 {SETTLEMENT_WITHDRAW_MAX_AMOUNT}",
            )

        if float(amt) < float(SETTLEMENT_WITHDRAW_MIN_AMOUNT):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"最低提现金额为 {SETTLEMENT_WITHDRAW_MIN_AMOUNT}",
            )

        if _quantize_amount(float(wallet.available_amount or 0.0)) < amt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="可提现余额不足")

        fee = _quantize_amount(float(SETTLEMENT_WITHDRAW_FEE))
        if fee < Decimal("0"):
            fee = Decimal("0")
        if fee > amt:
            fee = amt
        actual = amt - fee

        bank_res = await db.execute(
            select(LawyerBankAccount).where(
                LawyerBankAccount.id == int(bank_account_id),
                LawyerBankAccount.lawyer_id == int(lawyer_id),
                LawyerBankAccount.is_active,
            )
        )
        bank = bank_res.scalar_one_or_none()
        if bank is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="收款账户不存在")

        request_no = f"W{_now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

        raw_account_no = self._settlement.decrypt_secret(str(bank.account_no))
        encrypted_account_no = self._settlement.encrypt_secret(raw_account_no)

        account_info = {
            "account_type": str(bank.account_type),
            "bank_name": str(bank.bank_name or ""),
            "account_no": str(encrypted_account_no),
            "account_holder": str(bank.account_holder),
            "masked": {
                "account_no": _mask_account_no(str(raw_account_no)),
            },
        }

        wr = WithdrawalRequest(
            request_no=request_no,
            lawyer_id=int(lawyer_id),
            amount=float(amt),
            fee=float(fee),
            actual_amount=float(actual),
            amount_cents=_decimal_to_cents(amt),
            fee_cents=_decimal_to_cents(fee),
            actual_amount_cents=_decimal_to_cents(actual),
            withdraw_method=str(withdraw_method or "bank_card"),
            account_info=json.dumps(account_info, ensure_ascii=False),
            status="pending",
            created_at=_now(),
            updated_at=_now(),
        )

        wallet.available_amount = float(_quantize_amount(
            float(wallet.available_amount or 0.0)) - amt)
        wallet.frozen_amount = float(_quantize_amount(
            float(wallet.frozen_amount or 0.0)) + amt)
        _recalc_wallet_fields(wallet)

        db.add_all([wr, wallet])
        await db.commit()
        await db.refresh(wr)

        # 发送提现申请提交通知
        lawyer_res = await db.execute(select(Lawyer).where(Lawyer.id == int(lawyer_id)))
        lawyer = lawyer_res.scalar_one_or_none()
        if lawyer is not None and lawyer.user_id is not None:
            notification = Notification(
                user_id=int(lawyer.user_id),
                type=NotificationType.SYSTEM,
                title="提现申请已提交",
                content=f"您的提现申请已提交，金额：{float(amt):.2f}元，手续费：{float(fee):.2f}元，实际到账：{float(actual):.2f}元。请等待审核。",
                link="/lawyer/wallet",
                is_read=False,
            )
            db.add(notification)
            await db.commit()

        return wr

    async def admin_set_withdrawal_status(
        self,
        db: AsyncSession,
        *,
        withdrawal_id: int,
        action: str,
        admin_id: int,
        reject_reason: str | None = None,
        remark: str | None = None,
    ) -> WithdrawalRequest:
        """管理员设置提现状态（批准/驳回/完成/失败）"""
        res = await db.execute(select(WithdrawalRequest).where(WithdrawalRequest.id == int(withdrawal_id)))
        wr = res.scalar_one_or_none()
        if wr is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提现申请不存在")

        now = _now()
        cur = str(wr.status or "").lower()
        action_l = str(action).lower()

        wallet = await self._settlement.get_or_create_wallet(db, int(wr.lawyer_id))
        _recalc_wallet_fields(wallet)

        amt = _quantize_amount(float(wr.amount or 0.0))

        if action_l == "approve":
            if cur not in {"pending", "failed"}:
                raise HTTPException(status_code=400, detail="仅待审核可通过")
            wr.status = "approved"
            wr.admin_id = int(admin_id)
            wr.reviewed_at = now
            wr.remark = remark
            if cur == "failed":
                wallet.available_amount = float(_quantize_amount(
                    float(wallet.available_amount or 0.0)) - amt)
                if float(wallet.available_amount) < 0:
                    wallet.available_amount = 0.0
                wallet.frozen_amount = float(_quantize_amount(
                    float(wallet.frozen_amount or 0.0)) + amt)
                wr.reject_reason = None
        elif action_l == "reject":
            if cur != "pending":
                raise HTTPException(status_code=400, detail="仅待审核可驳回")
            wr.status = "rejected"
            wr.reject_reason = str(reject_reason or "").strip() or "驳回"
            wr.admin_id = int(admin_id)
            wr.reviewed_at = now
            wr.remark = remark

            wallet.frozen_amount = float(_quantize_amount(
                float(wallet.frozen_amount or 0.0)) - amt)
            if float(wallet.frozen_amount) < 0:
                wallet.frozen_amount = 0.0
            wallet.available_amount = float(_quantize_amount(
                float(wallet.available_amount or 0.0)) + amt)
        elif action_l == "complete":
            if cur != "approved":
                raise HTTPException(status_code=400, detail="仅已通过可标记完成")
            wr.status = "completed"
            wr.admin_id = int(admin_id)
            wr.completed_at = now
            wr.remark = remark

            wallet.frozen_amount = float(_quantize_amount(
                float(wallet.frozen_amount or 0.0)) - amt)
            if float(wallet.frozen_amount) < 0:
                wallet.frozen_amount = 0.0
            wallet.withdrawn_amount = float(_quantize_amount(
                float(wallet.withdrawn_amount or 0.0)) + amt)

            try:
                remaining = amt
                income_res = await db.execute(
                    select(LawyerIncomeRecord)
                    .where(
                        LawyerIncomeRecord.lawyer_id == int(wr.lawyer_id),
                        LawyerIncomeRecord.status.in_(
                            ["settled", "withdrawn"]),
                    )
                    .order_by(
                        func.coalesce(
                            LawyerIncomeRecord.settle_time,
                            LawyerIncomeRecord.created_at).asc(),
                        LawyerIncomeRecord.created_at.asc(),
                    )
                )
                records = income_res.scalars().all()
                for r in records:
                    if remaining <= Decimal("0"):
                        break

                    total_income = _quantize_amount(
                        float(r.lawyer_income or 0.0))
                    already = _quantize_amount(
                        float(r.withdrawn_amount or 0.0))
                    can_take = total_income - already
                    if can_take <= Decimal("0"):
                        if str(r.status or "").lower() == "settled":
                            r.status = "withdrawn"
                            db.add(r)
                        continue

                    take = can_take if can_take <= remaining else remaining
                    new_withdrawn = already + take
                    r.withdrawn_amount = float(new_withdrawn)
                    r.withdrawn_amount_cents = _decimal_to_cents(new_withdrawn)
                    if new_withdrawn >= total_income:
                        r.status = "withdrawn"
                    else:
                        r.status = "settled"
                    db.add(r)

                    remaining = remaining - take
            except Exception:
                pass
        elif action_l == "fail":
            if cur != "approved":
                raise HTTPException(status_code=400, detail="仅已通过可标记失败")
            wr.status = "failed"
            wr.admin_id = int(admin_id)
            wr.completed_at = now
            wr.remark = remark

            wallet.frozen_amount = float(_quantize_amount(
                float(wallet.frozen_amount or 0.0)) - amt)
            if float(wallet.frozen_amount) < 0:
                wallet.frozen_amount = 0.0
            wallet.available_amount = float(_quantize_amount(
                float(wallet.available_amount or 0.0)) + amt)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的操作: {action}")

        _recalc_wallet_fields(wallet)
        db.add_all([wr, wallet])
        await db.commit()
        await db.refresh(wr)

        # 发送提现状态变更通知
        lawyer_res = await db.execute(select(Lawyer).where(Lawyer.id == int(wr.lawyer_id)))
        lawyer = lawyer_res.scalar_one_or_none()
        if lawyer is not None and lawyer.user_id is not None:
            if action_l == "approve":
                notification = Notification(
                    user_id=int(lawyer.user_id),
                    type=NotificationType.SYSTEM,
                    title="提现申请已通过",
                    content=f"您的提现申请已通过审核，金额：{float(amt):.2f}元。正在处理打款，请耐心等待。",
                    link="/lawyer/wallet",
                    is_read=False,
                )
                db.add(notification)
            elif action_l == "reject":
                notification = Notification(
                    user_id=int(lawyer.user_id),
                    type=NotificationType.SYSTEM,
                    title="提现申请已驳回",
                    content=f"您的提现申请已被驳回，金额：{float(amt):.2f}元。驳回原因：{str(reject_reason or '无')}。资金已退回您的钱包。",
                    link="/lawyer/wallet",
                    is_read=False,
                )
                db.add(notification)
            elif action_l == "complete":
                notification = Notification(
                    user_id=int(lawyer.user_id),
                    type=NotificationType.SYSTEM,
                    title="提现已完成",
                    content=f"您的提现已完成，金额：{float(amt):.2f}元。款项已到账，请注意查收。",
                    link="/lawyer/wallet",
                    is_read=False,
                )
                db.add(notification)
            elif action_l == "fail":
                notification = Notification(
                    user_id=int(lawyer.user_id),
                    type=NotificationType.SYSTEM,
                    title="提现失败",
                    content=f"您的提现申请处理失败，金额：{float(amt):.2f}元。失败原因：{str(remark or '未知')}。资金已退回您的钱包，请重新申请。",
                    link="/lawyer/wallet",
                    is_read=False,
                )
                db.add(notification)
            await db.commit()

        return wr
