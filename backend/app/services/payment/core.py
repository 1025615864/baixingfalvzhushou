"""支付核心服务"""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...models.payment import (
    PaymentOrder, PaymentStatus, PaymentMethod,
    UserBalance, BalanceTransaction
)
from ...models.user import User

logger = logging.getLogger(__name__)


class PaymentCoreService:
    """支付核心服务"""

    @staticmethod
    def generate_order_no() -> str:
        """生成订单号"""
        # 格式: ORD + 年月日 + 8位随机数
        now = datetime.now()
        random_part = secrets.token_hex(4).upper()
        return f"ORD{now.strftime('%Y%m%d')}{random_part}"

    @staticmethod
    def generate_refund_no() -> str:
        """生成退款单号"""
        now = datetime.now()
        random_part = secrets.token_hex(4).upper()
        return f"RFD{now.strftime('%Y%m%d')}{random_part}"

    @classmethod
    async def create_order(
        cls,
        db: AsyncSession,
        user_id: int,
        order_type: str,
        amount: float,
        title: str,
        description: Optional[str] = None,
        payment_method: Optional[str] = None,
        related_id: Optional[int] = None,
        related_type: Optional[str] = None,
        expires_in_minutes: int = 30
    ) -> PaymentOrder:
        """创建支付订单"""
        order = PaymentOrder(
            order_no=cls.generate_order_no(),
            user_id=user_id,
            order_type=order_type,
            amount=amount,
            actual_amount=amount,  # 可在此添加优惠逻辑
            amount_cents=int(amount * 100),
            actual_amount_cents=int(amount * 100),
            status=PaymentStatus.PENDING,
            payment_method=payment_method,
            title=title,
            description=description,
            related_id=related_id,
            related_type=related_type,
            expires_at=datetime.now() + timedelta(minutes=expires_in_minutes)
        )

        db.add(order)
        await db.flush()
        await db.refresh(order)

        logger.info(f"Created payment order: {order.order_no} for user {user_id}")
        return order

    @classmethod
    async def get_order_by_no(
        cls,
        db: AsyncSession,
        order_no: str
    ) -> Optional[PaymentOrder]:
        """根据订单号获取订单"""
        result = await db.execute(
            select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def mark_order_paid(
        cls,
        db: AsyncSession,
        order: PaymentOrder,
        trade_no: str,
        paid_at: Optional[datetime] = None
    ) -> PaymentOrder:
        """标记订单为已支付"""
        order.status = PaymentStatus.PAID
        order.trade_no = trade_no
        order.paid_at = paid_at or datetime.now()

        await db.flush()
        await db.refresh(order)

        logger.info(f"Order marked as paid: {order.order_no}, trade_no: {trade_no}")
        return order

    @classmethod
    async def cancel_order(
        cls,
        db: AsyncSession,
        order: PaymentOrder,
        reason: Optional[str] = None
    ) -> PaymentOrder:
        """取消订单"""
        if order.status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot cancel order with status: {order.status}")

        order.status = PaymentStatus.CANCELLED

        await db.flush()
        await db.refresh(order)

        logger.info(f"Order cancelled: {order.order_no}, reason: {reason}")
        return order

    @classmethod
    async def get_user_orders(
        cls,
        db: AsyncSession,
        user_id: int,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[PaymentOrder], int]:
        """获取用户订单列表"""
        query = select(PaymentOrder).where(PaymentOrder.user_id == user_id)

        if status:
            query = query.where(PaymentOrder.status == status)

        # 获取总数
        count_query = select(PaymentOrder).where(PaymentOrder.user_id == user_id)
        if status:
            count_query = count_query.where(PaymentOrder.status == status)
        total_result = await db.execute(
            select(PaymentOrder).select_from(count_query.subquery())
        )
        total = len(total_result.scalars().all())

        # 分页
        query = query.order_by(PaymentOrder.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        orders = list(result.scalars().all())

        return orders, total

    @classmethod
    async def get_or_create_user_balance(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> UserBalance:
        """获取或创建用户余额"""
        result = await db.execute(
            select(UserBalance).where(UserBalance.user_id == user_id)
        )
        balance = result.scalar_one_or_none()

        if not balance:
            balance = UserBalance(user_id=user_id)
            db.add(balance)
            await db.flush()
            await db.refresh(balance)

        return balance

    @classmethod
    async def recharge_balance(
        cls,
        db: AsyncSession,
        user_id: int,
        amount: float,
        order_id: int,
        description: Optional[str] = None
    ) -> UserBalance:
        """充值余额"""
        balance = await cls.get_or_create_user_balance(db, user_id)

        # 记录交易前余额
        balance_before = balance.balance

        # 更新余额
        balance.balance += amount
        balance.total_recharged += amount
        balance.balance_cents = int(balance.balance * 100)
        balance.total_recharged_cents = int(balance.total_recharged * 100)

        # 创建交易记录
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
            description=description or "余额充值"
        )
        db.add(transaction)

        await db.flush()
        await db.refresh(balance)

        logger.info(f"Balance recharged: user={user_id}, amount={amount}")
        return balance

    @classmethod
    async def consume_balance(
        cls,
        db: AsyncSession,
        user_id: int,
        amount: float,
        order_id: int,
        description: Optional[str] = None
    ) -> UserBalance:
        """消费余额"""
        balance = await cls.get_or_create_user_balance(db, user_id)

        if balance.balance < amount:
            raise ValueError("Insufficient balance")

        # 记录交易前余额
        balance_before = balance.balance

        # 更新余额
        balance.balance -= amount
        balance.total_consumed += amount
        balance.balance_cents = int(balance.balance * 100)
        balance.total_consumed_cents = int(balance.total_consumed * 100)

        # 创建交易记录
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
            description=description or "余额消费"
        )
        db.add(transaction)

        await db.flush()
        await db.refresh(balance)

        logger.info(f"Balance consumed: user={user_id}, amount={amount}")
        return balance

    @classmethod
    async def deduct_balance_for_refund(
        cls,
        db: AsyncSession,
        user_id: int,
        amount: float,
        order_id: int,
        description: Optional[str] = None
    ) -> UserBalance:
        """退款时扣减余额（用于充值订单退款）"""
        balance = await cls.get_or_create_user_balance(db, user_id)

        if balance.balance < amount:
            raise ValueError("Insufficient balance for refund deduction")

        # 记录交易前余额
        balance_before = balance.balance

        # 更新余额
        balance.balance -= amount
        balance.total_recharged -= amount  # 减少累计充值
        balance.balance_cents = int(balance.balance * 100)
        balance.total_recharged_cents = int(balance.total_recharged * 100)

        # 创建交易记录
        transaction = BalanceTransaction(
            user_id=user_id,
            order_id=order_id,
            type="refund",
            amount=-amount,
            amount_cents=int(-amount * 100),
            balance_before=balance_before,
            balance_after=balance.balance,
            balance_before_cents=int(balance_before * 100),
            balance_after_cents=int(balance.balance * 100),
            description=description or "充值订单退款扣减余额"
        )
        db.add(transaction)

        await db.flush()
        await db.refresh(balance)

        logger.info(f"Balance deducted for refund: user={user_id}, amount={amount}")
        return balance
