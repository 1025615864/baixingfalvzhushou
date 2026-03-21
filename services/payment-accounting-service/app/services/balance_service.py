"""余额服务"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import UserBalance, BalanceTransaction


class BalanceService:
    """余额服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_balance(self, user_id: int) -> UserBalance:
        """获取或创建用户余额"""
        result = await self.db.execute(
            select(UserBalance).where(UserBalance.user_id == user_id)
        )
        balance = result.scalar_one_or_none()

        if not balance:
            balance = UserBalance(user_id=user_id)
            self.db.add(balance)
            await self.db.commit()
            await self.db.refresh(balance)

        return balance

    async def recharge(
        self,
        user_id: int,
        amount: float,
        order_id: int,
        description: str = "余额充值"
    ) -> UserBalance:
        """充值余额"""
        balance = await self.get_or_create_balance(user_id)
        balance_before = balance.balance

        balance.balance += amount
        balance.total_recharged += amount
        balance.balance_cents = int(balance.balance * 100)
        balance.total_recharged_cents = int(balance.total_recharged * 100)

        transaction = BalanceTransaction(
            user_id=user_id,
            order_id=order_id,
            type="recharge",
            amount=amount,
            amount_cents=int(amount * 100),
            balance_before=balance_before,
            balance_after=balance.balance,
            balance_before_cents=int(balance_before * 100),
            balance_after_cents=int(balance.balance * 100),
            description=description,
        )
        self.db.add(transaction)

        await self.db.commit()
        await self.db.refresh(balance)
        return balance

    async def consume(
        self,
        user_id: int,
        amount: float,
        order_id: int,
        description: str = "余额消费"
    ) -> UserBalance:
        """消费余额（原子操作）"""
        balance = await self.get_or_create_balance(user_id)

        if balance.balance < amount:
            raise ValueError("Insufficient balance")

        balance_before = balance.balance
        balance.balance -= amount
        balance.total_consumed += amount
        balance.balance_cents = int(balance.balance * 100)
        balance.total_consumed_cents = int(balance.total_consumed * 100)

        transaction = BalanceTransaction(
            user_id=user_id,
            order_id=order_id,
            type="consume",
            amount=-amount,
            amount_cents=int(-amount * 100),
            balance_before=balance_before,
            balance_after=balance.balance,
            balance_before_cents=int(balance_before * 100),
            balance_after_cents=int(balance.balance * 100),
            description=description,
        )
        self.db.add(transaction)

        await self.db.commit()
        await self.db.refresh(balance)
        return balance

    async def get_transactions(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BalanceTransaction], int]:
        """获取余额变动记录"""
        query = (
            select(BalanceTransaction)
            .where(BalanceTransaction.user_id == user_id)
            .order_by(BalanceTransaction.created_at.desc())
        )

        total_result = await self.db.execute(
            select(BalanceTransaction.id).where(BalanceTransaction.user_id == user_id)
        )
        total = len(total_result.scalars().all())

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        transactions = result.scalars().all()

        return list(transactions), total
