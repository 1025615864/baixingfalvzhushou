"""结算服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import LawyerWallet, Settlement


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
