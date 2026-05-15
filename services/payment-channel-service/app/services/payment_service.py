"""支付服务编排层 - 统一管理支付创建、回调处理、退款流程"""
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.payment import PaymentOrder, PaymentCallback, PaymentRefund
from ..models.admin import ChannelConfig, PaymentAuditLog


class PaymentService:
    async def create_payment(
        self,
        db: AsyncSession,
        order_no: str,
        user_id: int,
        order_type: str,
        amount: float,
        title: str,
        description: str = "",
        payment_method: str = "wechat",
        related_id: int = None,
        related_type: str = None,
    ) -> PaymentOrder:
        channel = await self._get_enabled_channel(db, payment_method)
        if not channel:
            raise ValueError(f"支付渠道 {payment_method} 不可用")

        order = PaymentOrder(
            order_no=order_no,
            user_id=user_id,
            order_type=order_type,
            amount=amount,
            actual_amount=amount,
            amount_cents=int(amount * 100),
            actual_amount_cents=int(amount * 100),
            status="pending",
            payment_method=payment_method,
            title=title,
            description=description,
            related_id=related_id,
            related_type=related_type,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        db.add(order)
        await db.flush()
        return order

    async def process_callback(
        self,
        db: AsyncSession,
        order_no: str,
        provider: str,
        callback_no: str,
        status: str,
        raw_payload: dict,
    ) -> PaymentOrder:
        result = await db.execute(
            select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError(f"订单 {order_no} 不存在")

        callback = PaymentCallback(
            order_no=order_no,
            provider=provider,
            callback_no=callback_no,
            status=status,
            raw_payload=json.dumps(raw_payload, ensure_ascii=False),
            processed_at=datetime.now(timezone.utc),
        )
        db.add(callback)

        if status == "success" and order.status == "pending":
            order.status = "paid"
            order.paid_at = datetime.now(timezone.utc)
            if callback_no:
                order.trade_no = callback_no

            audit = PaymentAuditLog(
                target_id=order.id,
                operator_id=0,
                operator_name="system",
                action="payment_success",
                comment=f"支付成功: {provider} {callback_no}",
                extra_data={"provider": provider, "callback_no": callback_no},
            )
            db.add(audit)

        await db.flush()
        return order

    async def refund(
        self,
        db: AsyncSession,
        order_no: str,
        amount: float,
        reason: str = "",
        operator_id: int = 0,
        operator_name: str = "",
    ) -> PaymentRefund:
        result = await db.execute(
            select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError(f"订单 {order_no} 不存在")
        if order.status not in ("paid", "completed"):
            raise ValueError(f"订单状态 {order.status} 不允许退款")

        refund_no = f"RF{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{order.id:06d}"
        refund = PaymentRefund(
            order_no=order_no,
            refund_no=refund_no,
            amount=amount,
            reason=reason,
            status="pending",
            provider=order.payment_method,
        )
        db.add(refund)

        audit = PaymentAuditLog(
            target_id=order.id,
            operator_id=operator_id,
            operator_name=operator_name,
            action="refund_requested",
            comment=f"申请退款: {amount} 原因: {reason}",
            extra_data={"refund_no": refund_no, "amount": amount},
        )
        db.add(audit)

        await db.flush()
        return refund

    async def query_payment_status(self, db: AsyncSession, order_no: str) -> dict:
        result = await db.execute(
            select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError(f"订单 {order_no} 不存在")
        return {
            "order_no": order.order_no,
            "status": order.status,
            "amount": float(order.actual_amount) if order.actual_amount else 0,
            "payment_method": order.payment_method,
            "trade_no": order.trade_no,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        }

    async def _get_enabled_channel(self, db: AsyncSession, channel_code: str) -> Optional[ChannelConfig]:
        result = await db.execute(
            select(ChannelConfig).where(
                ChannelConfig.channel_code == channel_code,
                ChannelConfig.enabled == True,
            )
        )
        return result.scalar_one_or_none()
