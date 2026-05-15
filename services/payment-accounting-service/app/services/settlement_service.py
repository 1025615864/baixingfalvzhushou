"""结算服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models import LawyerWallet, Settlement
from ..models.admin import SettlementAudit


class SettlementService:
    """结算服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_wallet(self, lawyer_id: int) -> LawyerWallet:
        """获取或创建律师钱包"""
        result = await self.db.execute(
            select(LawyerWallet).where(LawyerWallet.lawyer_id == lawyer_id)
        )
        wallet = result.scalar_one_or_none()

        if not wallet:
            wallet = LawyerWallet(lawyer_id=lawyer_id)
            self.db.add(wallet)
            await self.db.commit()
            await self.db.refresh(wallet)

        return wallet

    async def withdraw(
        self,
        lawyer_id: int,
        amount: float,
        bank_account: str,
        real_name: str,
    ) -> dict:
        """申请提现"""
        wallet = await self.get_or_create_wallet(lawyer_id)

        if wallet.balance < amount:
            raise ValueError("Insufficient balance")

        # 创建结算记录
        settlement = Settlement(
            lawyer_id=lawyer_id,
            total_amount=amount,
            total_amount_cents=int(amount * 100),
            platform_fee=amount * 0.05,  # 5% 平台费
            platform_fee_cents=int(amount * 0.05 * 100),
            settle_amount=amount * 0.95,
            settle_amount_cents=int(amount * 0.95 * 100),
            status="pending",
        )
        self.db.add(settlement)

        # 冻结金额
        wallet.balance -= amount
        wallet.balance_cents = int(wallet.balance * 100)

        await self.db.commit()
        await self.db.refresh(settlement)

        return {
            "settlement_id": settlement.id,
            "amount": amount,
            "fee": float(settlement.platform_fee),
            "actual_amount": float(settlement.settle_amount),
            "status": settlement.status,
        }

    async def approve_settlement(self, settlement_id: int, auditor_id: int, auditor_name: str, comment: str = "") -> Settlement:
        result = await self.db.execute(select(Settlement).where(Settlement.id == settlement_id))
        settlement = result.scalar_one_or_none()
        if not settlement:
            raise ValueError("结算单不存在")
        if settlement.status != "pending":
            raise ValueError(f"结算单状态为 {settlement.status}，无法审批")
        settlement.status = "approved"
        audit = SettlementAudit(
            settlement_id=settlement_id,
            auditor_id=auditor_id,
            auditor_name=auditor_name,
            action="approve",
            comment=comment or "审批通过",
        )
        self.db.add(audit)
        await self.db.flush()
        return settlement

    async def reject_settlement(self, settlement_id: int, auditor_id: int, auditor_name: str, reason: str = "") -> Settlement:
        result = await self.db.execute(select(Settlement).where(Settlement.id == settlement_id))
        settlement = result.scalar_one_or_none()
        if not settlement:
            raise ValueError("结算单不存在")
        if settlement.status != "pending":
            raise ValueError(f"结算单状态为 {settlement.status}，无法拒绝")
        settlement.status = "rejected"
        audit = SettlementAudit(
            settlement_id=settlement_id,
            auditor_id=auditor_id,
            auditor_name=auditor_name,
            action="reject",
            comment=reason or "审批拒绝",
        )
        self.db.add(audit)
        await self.db.flush()
        return settlement

    async def list_settlements(self, status: str = None, lawyer_id: int = None, page: int = 1, page_size: int = 20) -> dict:
        filters = []
        if status:
            filters.append(Settlement.status == status)
        if lawyer_id:
            filters.append(Settlement.lawyer_id == lawyer_id)
        count_stmt = select(func.count(Settlement.id)).where(*filters)
        total = (await self.db.execute(count_stmt)).scalar_one()
        stmt = select(Settlement).where(*filters).order_by(Settlement.created_at.desc()).offset((page-1)*page_size).limit(page_size)
        result = await self.db.execute(stmt)
        settlements = result.scalars().all()
        return {"items": settlements, "total": total, "page": page, "page_size": page_size}
