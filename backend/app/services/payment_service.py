"""支付服务"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.payment import BalanceTransaction, PaymentMethod, PaymentOrder, PaymentStatus, UserBalance
from ..models.lawfirm import LawyerConsultation


class PaymentService:
    async def create_order(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        amount: float,
        order_type: str,
        description: str | None = None,
        title: str | None = None,
    ) -> PaymentOrder:
        order = PaymentOrder(
            order_no=str(uuid.uuid4()),
            user_id=int(user_id),
            order_type=str(order_type),
            amount=float(amount),
            actual_amount=float(amount),
            status=PaymentStatus.PENDING,
            title=title or "支付订单",
            description=description,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    async def process_payment(
        self,
        db: AsyncSession,
        *,
        order_no: str,
        payment_method: str,
    ) -> PaymentOrder:
        result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == str(order_no)))
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("订单不存在")
        if order.status == PaymentStatus.PAID:
            return order

        method = payment_method.value if hasattr(payment_method, 'value') else str(payment_method)
        if method == PaymentMethod.BALANCE.value:
            balance_res = await db.execute(
                select(UserBalance).where(
                    UserBalance.user_id == int(
                        order.user_id))
            )
            balance = balance_res.scalar_one_or_none()
            if not balance or float(balance.balance or 0.0) < float(
                    order.actual_amount):
                raise ValueError("余额不足")
            before = float(balance.balance)
            balance.balance = before - float(order.actual_amount)
            transaction = BalanceTransaction(
                user_id=int(order.user_id),
                order_id=int(order.id),
                type="consume",
                amount=-float(order.actual_amount),
                balance_before=before,
                balance_after=float(balance.balance),
                description=f"支付订单 {order.order_no}",
            )
            db.add(transaction)

        order.status = PaymentStatus.PAID
        order.payment_method = method
        order.paid_at = datetime.now(timezone.utc)

        # 如果是咨询订单，更新咨询状态为confirmed
        if order.order_type == "consultation" and order.related_id:
            consultation_result = await db.execute(
                select(LawyerConsultation).where(
                    LawyerConsultation.id == order.related_id)
            )
            consultation = consultation_result.scalar_one_or_none()
            if consultation and consultation.status == "pending":
                consultation.status = "confirmed"

        await db.commit()
        await db.refresh(order)
        return order

    async def refund_payment(
        self,
        db: AsyncSession,
        *,
        order_no: str,
    ) -> PaymentOrder:
        """退款"""
        result = await db.execute(select(PaymentOrder).where(PaymentOrder.order_no == str(order_no)))
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("订单不存在")
        if order.status != PaymentStatus.PAID:
            raise ValueError("订单未支付或已退款")

        # 退款到余额
        balance_res = await db.execute(
            select(UserBalance).where(
                UserBalance.user_id == int(
                    order.user_id))
        )
        balance = balance_res.scalar_one_or_none()
        if not balance:
            raise ValueError("用户余额不存在")

        before = float(balance.balance)
        balance.balance = before + float(order.actual_amount)
        transaction = BalanceTransaction(
            user_id=int(order.user_id),
            order_id=int(order.id),
            type="refund",
            amount=float(order.actual_amount),
            balance_before=before,
            balance_after=float(balance.balance),
            description=f"退款订单 {order.order_no}",
        )
        db.add(transaction)

        order.status = PaymentStatus.REFUNDED
        await db.commit()
        await db.refresh(order)
        return order


payment_service = PaymentService()
