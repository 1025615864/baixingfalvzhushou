"""结算服务核心模块

包含：
- 常量定义（费率、限制）
- 工具函数
- SettlementService 主类（加密、费率计算、结算管理）
"""
from __future__ import annotations

import json
import os
import base64
import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...models.lawfirm import Lawyer, LawyerConsultation
from ...models.notification import Notification, NotificationType
from ...models.payment import PaymentOrder, PaymentStatus, Settlement
from ...models.settlement import LawyerBankAccount, LawyerIncomeRecord, LawyerWallet, WithdrawalRequest
from ...models.user import User


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _quantize_amount(amount: float) -> Decimal:
    return Decimal(str(amount)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal_to_cents(amount: Decimal) -> int:
    return int(amount * 100)


def _get_float_env(key: str, default: float) -> float:
    raw = os.getenv(key, "").strip()
    if not raw:
        return float(default)
    try:
        return float(raw)
    except Exception:
        return float(default)


def _get_int_env(key: str, default: int) -> int:
    raw = os.getenv(key, "").strip()
    if not raw:
        return int(default)
    try:
        return int(raw)
    except Exception:
        return int(default)


def _get_int_set_env(key: str) -> set[int]:
    raw = os.getenv(key, "").strip()
    if not raw:
        return set()
    out: set[int] = set()
    for part in raw.split(","):
        p = str(part).strip()
        if not p:
            continue
        try:
            out.add(int(p))
        except Exception:
            continue
    return out


# === 结算常量 ===

SETTLEMENT_PLATFORM_FEE_RATE = _get_float_env(
    "SETTLEMENT_PLATFORM_FEE_RATE", 0.15)
SETTLEMENT_FREEZE_DAYS = _get_int_env("SETTLEMENT_FREEZE_DAYS", 7)
SETTLEMENT_WITHDRAW_MIN_AMOUNT = _get_float_env(
    "SETTLEMENT_WITHDRAW_MIN_AMOUNT", 100.0)
SETTLEMENT_WITHDRAW_MAX_AMOUNT = _get_float_env(
    "SETTLEMENT_WITHDRAW_MAX_AMOUNT", 50000.0)
SETTLEMENT_WITHDRAW_FEE = _get_float_env("SETTLEMENT_WITHDRAW_FEE", 0.0)

SETTLEMENT_VERIFIED_MIN_COMPLETED = _get_int_env(
    "SETTLEMENT_VERIFIED_MIN_COMPLETED", 10)
SETTLEMENT_VERIFIED_MIN_RATING = _get_float_env(
    "SETTLEMENT_VERIFIED_MIN_RATING", 4.5)
SETTLEMENT_VERIFIED_PLATFORM_FEE_RATE = _get_float_env(
    "SETTLEMENT_VERIFIED_PLATFORM_FEE_RATE", 0.13
)
SETTLEMENT_VERIFIED_FREEZE_DAYS = _get_int_env(
    "SETTLEMENT_VERIFIED_FREEZE_DAYS", 5)

SETTLEMENT_GOLD_MIN_COMPLETED = _get_int_env(
    "SETTLEMENT_GOLD_MIN_COMPLETED", 50)
SETTLEMENT_GOLD_MIN_RATING = _get_float_env("SETTLEMENT_GOLD_MIN_RATING", 4.8)
SETTLEMENT_GOLD_PLATFORM_FEE_RATE = _get_float_env(
    "SETTLEMENT_GOLD_PLATFORM_FEE_RATE", 0.10)
SETTLEMENT_GOLD_FREEZE_DAYS = _get_int_env("SETTLEMENT_GOLD_FREEZE_DAYS", 3)

SETTLEMENT_PARTNER_LAWYER_IDS = _get_int_set_env(
    "SETTLEMENT_PARTNER_LAWYER_IDS")
SETTLEMENT_PARTNER_PLATFORM_FEE_RATE = _get_float_env(
    "SETTLEMENT_PARTNER_PLATFORM_FEE_RATE", 0.08
)
SETTLEMENT_PARTNER_FREEZE_DAYS = _get_int_env(
    "SETTLEMENT_PARTNER_FREEZE_DAYS", 1)


def _mask_account_no(account_no: str) -> str:
    s = str(account_no or "").strip()
    if len(s) <= 4:
        return "****"
    return f"****{s[-4:]}"


_ENC_PREFIX = "enc:"


def _get_fernet() -> Fernet:
    secret = str(get_settings().secret_key or "")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def _recalc_wallet_fields(wallet: LawyerWallet) -> None:
    """重新计算钱包字段"""
    total = _quantize_amount(float(wallet.total_income or 0.0))
    withdrawn = _quantize_amount(float(wallet.withdrawn_amount or 0.0))
    pending = _quantize_amount(float(wallet.pending_amount or 0.0))
    frozen = _quantize_amount(float(wallet.frozen_amount or 0.0))

    available = total - withdrawn - pending - frozen
    if available < Decimal("0"):
        available = Decimal("0")

    wallet.available_amount = float(available)
    wallet.total_income_cents = _decimal_to_cents(total)
    wallet.withdrawn_amount_cents = _decimal_to_cents(withdrawn)
    wallet.pending_amount_cents = _decimal_to_cents(pending)
    wallet.frozen_amount_cents = _decimal_to_cents(frozen)
    wallet.available_amount_cents = _decimal_to_cents(available)


class SettlementService:
    """结算服务主类"""

    def encrypt_secret(self, raw: str) -> str:
        """加密敏感信息"""
        s = str(raw or "").strip()
        if not s:
            return ""
        if s.startswith(_ENC_PREFIX):
            return s
        token = _get_fernet().encrypt(s.encode("utf-8")).decode("utf-8")
        return f"{_ENC_PREFIX}{token}"

    def decrypt_secret(self, value: str) -> str:
        """解密敏感信息"""
        s = str(value or "").strip()
        if not s:
            return ""
        if not s.startswith(_ENC_PREFIX):
            return s
        token = s[len(_ENC_PREFIX):]
        try:
            return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            return ""
        except Exception:
            return ""

    def choose_platform_fee_rate(
            self, lawyer_id: int, rating: float, completed: int) -> float:
        """根据律师等级选择平台费率"""
        if int(lawyer_id) in SETTLEMENT_PARTNER_LAWYER_IDS:
            return float(SETTLEMENT_PARTNER_PLATFORM_FEE_RATE)

        if completed >= int(SETTLEMENT_GOLD_MIN_COMPLETED) and rating >= float(
                SETTLEMENT_GOLD_MIN_RATING):
            return float(SETTLEMENT_GOLD_PLATFORM_FEE_RATE)
        if completed >= int(SETTLEMENT_VERIFIED_MIN_COMPLETED) and rating >= float(
                SETTLEMENT_VERIFIED_MIN_RATING):
            return float(SETTLEMENT_VERIFIED_PLATFORM_FEE_RATE)

        return float(SETTLEMENT_PLATFORM_FEE_RATE)

    def choose_freeze_days(self, lawyer_id: int,
                           rating: float, completed: int) -> int:
        """根据律师等级选择冻结期天数"""
        if int(lawyer_id) in SETTLEMENT_PARTNER_LAWYER_IDS:
            return int(SETTLEMENT_PARTNER_FREEZE_DAYS)

        if completed >= int(SETTLEMENT_GOLD_MIN_COMPLETED) and rating >= float(
                SETTLEMENT_GOLD_MIN_RATING):
            return int(SETTLEMENT_GOLD_FREEZE_DAYS)
        if completed >= int(SETTLEMENT_VERIFIED_MIN_COMPLETED) and rating >= float(
                SETTLEMENT_VERIFIED_MIN_RATING):
            return int(SETTLEMENT_VERIFIED_FREEZE_DAYS)

        return int(SETTLEMENT_FREEZE_DAYS)

    async def get_platform_fee_rate(
            self, db: AsyncSession, lawyer_id: int) -> float:
        """获取律师的平台费率"""
        res = await db.execute(select(Lawyer).where(Lawyer.id == int(lawyer_id)))
        lawyer = res.scalar_one_or_none()
        if lawyer is None:
            return float(SETTLEMENT_PLATFORM_FEE_RATE)

        rating = float(getattr(lawyer, "rating", 0.0) or 0.0)
        completed_res = await db.execute(
            select(func.count(LawyerConsultation.id)).where(
                LawyerConsultation.lawyer_id == int(lawyer_id),
                LawyerConsultation.status == "completed",
            )
        )
        completed = int(completed_res.scalar() or 0)

        return self.choose_platform_fee_rate(
            int(lawyer_id), float(rating), int(completed))

    async def get_freeze_days(self, db: AsyncSession, lawyer_id: int) -> int:
        """获取律师的冻结期天数"""
        res = await db.execute(select(Lawyer).where(Lawyer.id == int(lawyer_id)))
        lawyer = res.scalar_one_or_none()
        if lawyer is None:
            return int(SETTLEMENT_FREEZE_DAYS)

        rating = float(getattr(lawyer, "rating", 0.0) or 0.0)
        completed_res = await db.execute(
            select(func.count(LawyerConsultation.id)).where(
                LawyerConsultation.lawyer_id == int(lawyer_id),
                LawyerConsultation.status == "completed",
            )
        )
        completed = int(completed_res.scalar() or 0)

        return self.choose_freeze_days(
            int(lawyer_id), float(rating), int(completed))

    async def get_current_lawyer(
            self, db: AsyncSession, user_id: int) -> Lawyer | None:
        """获取当前登录律师"""
        res = await db.execute(
            select(Lawyer).where(
                Lawyer.user_id == int(user_id),
                Lawyer.is_active,
            )
        )
        return res.scalar_one_or_none()

    async def get_or_create_wallet(
            self, db: AsyncSession, lawyer_id: int) -> LawyerWallet:
        """获取或创建钱包"""
        res = await db.execute(select(LawyerWallet).where(LawyerWallet.lawyer_id == int(lawyer_id)))
        wallet = res.scalar_one_or_none()
        if wallet is not None:
            _recalc_wallet_fields(wallet)
            return wallet

        wallet = LawyerWallet(lawyer_id=int(lawyer_id))
        _recalc_wallet_fields(wallet)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
        return wallet

    async def create_settlement(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        amount: float,
        period: str,
        description: str | None = None,
    ) -> Settlement:
        """创建结算记录"""
        settlement = Settlement(
            user_id=int(user_id),
            amount=float(amount),
            period=str(period),
            description=description,
            status="pending",
        )
        db.add(settlement)
        await db.commit()
        await db.refresh(settlement)
        return settlement

    async def get_settlement_list(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ):
        """获取结算列表"""
        query = (
            select(Settlement)
            .where(Settlement.user_id == int(user_id))
            .order_by(Settlement.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(query)
        items = list(result.scalars().all())
        total = int(
            (await db.execute(select(func.count(Settlement.id)).where(Settlement.user_id == int(user_id))))
            .scalar()
            or 0
        )
        return type(
            "SettlementList", (), {
                "items": items, "total": total, "page": page, "page_size": page_size})

    async def get_settlement_detail(
            self,
            db: AsyncSession,
            *,
            settlement_id: int) -> Settlement | None:
        """获取结算详情"""
        result = await db.execute(select(Settlement).where(Settlement.id == int(settlement_id)))
        return result.scalar_one_or_none()

    async def update_status(
        self,
        db: AsyncSession,
        *,
        settlement_id: int,
        new_status: str,
    ) -> Settlement:
        """更新结算状态"""
        settlement = await self.get_settlement_detail(db, settlement_id=int(settlement_id))
        if settlement is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="结算不存在")
        settlement.status = str(new_status)
        await db.commit()
        await db.refresh(settlement)
        return settlement

    async def calculate_amount(
        self,
        db: AsyncSession,
        *,
        lawyer_id: int,
        start_date: str,
        end_date: str,
    ) -> float:
        """计算结算金额"""
        result = await db.execute(
            select(func.sum(LawyerIncomeRecord.lawyer_income)).where(
                LawyerIncomeRecord.lawyer_id == int(lawyer_id)
            )
        )
        return float(result.scalar() or 0.0)

    async def generate_report(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        start_date: str,
        end_date: str,
    ):
        """生成结算报告"""
        result = await db.execute(select(Settlement).where(Settlement.user_id == int(user_id)))
        items = list(result.scalars().all())
        total_amount = float(sum(float(s.amount or 0.0) for s in items))
        return type(
            "SettlementReport", (), {
                "total_amount": total_amount, "settlement_count": len(items)})

    def calculate_platform_fee(self, amount: float) -> float:
        """计算平台费"""
        return float(amount) * float(SETTLEMENT_PLATFORM_FEE_RATE)

    def calculate_tax_deduction(self, amount: float) -> float:
        """计算税费扣减"""
        return float(amount) * 0.03

    def calculate_net_amount(self, amount: float) -> float:
        """计算净到账金额"""
        platform_fee = self.calculate_platform_fee(amount)
        tax = self.calculate_tax_deduction(amount)
        net = float(amount) - platform_fee - tax
        return max(0.0, net)

    # === 向后兼容代理方法 ===

    async def ensure_income_record_for_completed_consultation(
        self,
        db: AsyncSession,
        consultation: LawyerConsultation,
        order: PaymentOrder | None,
    ) -> LawyerIncomeRecord | None:
        """确保咨询完成后的收入记录（向后兼容）"""
        from .income import IncomeService

        income_service = IncomeService(self)
        return await income_service.ensure_income_record_for_completed_consultation(db, consultation, order)

    async def ensure_income_record_for_paid_review_order(
        self,
        db: AsyncSession,
        *,
        lawyer_id: int,
        order: PaymentOrder,
    ) -> LawyerIncomeRecord | None:
        """确保已支付审核订单的收入记录（向后兼容）"""
        from .income import IncomeService

        income_service = IncomeService(self)
        return await income_service.ensure_income_record_for_paid_review_order(db, lawyer_id=lawyer_id, order=order)

    async def settle_due_income_records(
            self, db: AsyncSession) -> dict[str, int]:
        """结算到期的收入记录（向后兼容）"""
        from .income import IncomeService

        income_service = IncomeService(self)
        return await income_service.settle_due_income_records(db)

    async def withdraw(
        self,
        db: AsyncSession,
        *,
        settlement_id: int,
        bank_account: str,
    ) -> bool:
        """提现（向后兼容）"""
        settlement = await self.get_settlement_detail(db, settlement_id=int(settlement_id))
        if settlement is None:
            return False
        settlement.status = "withdrawn"
        await db.commit()
        return True

    async def create_withdrawal_request(
        self,
        db: AsyncSession,
        *,
        lawyer_id: int,
        amount: float,
        withdraw_method: str,
        bank_account_id: int,
    ) -> WithdrawalRequest:
        """创建提现申请（向后兼容）"""
        from .withdrawal import WithdrawalService

        withdrawal_service = WithdrawalService(self)
        return await withdrawal_service.create_withdrawal_request(
            db, lawyer_id=lawyer_id, amount=amount, withdraw_method=withdraw_method, bank_account_id=bank_account_id
        )

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
        """管理员设置提现状态（向后兼容）"""
        from .withdrawal import WithdrawalService

        withdrawal_service = WithdrawalService(self)
        return await withdrawal_service.admin_set_withdrawal_status(
            db,
            withdrawal_id=withdrawal_id,
            action=action,
            admin_id=admin_id,
            reject_reason=reject_reason,
            remark=remark,
        )
