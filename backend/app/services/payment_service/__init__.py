from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import (
    PaymentOrder,
    PaymentStatus,
    PaymentMethod,
    OrderType,
    UserBalance,
    BalanceTransaction,
    PaymentCallbackEvent,
)
from app.models.lawfirm import LawyerConsultation
from app.models.user import User


class PaymentService:
    VALID_ORDER_TYPES = {"consultation", "service", "vip", "recharge", "light_consult_review", "ai_pack"}

    async def create_order(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        order_type: str,
        title: str = "支付订单",
        description: str | None = None,
        related_id: int | None = None,
        related_type: str | None = None,
    ) -> PaymentOrder:
        if amount <= 0:
            raise ValueError("订单金额必须大于 0")
        if order_type not in self.VALID_ORDER_TYPES:
            raise ValueError(f"无效的订单类型: {order_type}")

        order_no = f"ORD{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
        order = PaymentOrder(
            order_no=order_no,
            user_id=user_id,
            order_type=order_type,
            amount=amount,
            actual_amount=amount,
            status=PaymentStatus.PENDING.value,
            title=title,
            description=description,
            related_id=related_id,
            related_type=related_type,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    async def process_payment(
        self,
        db: AsyncSession,
        order_no: str,
        payment_method: PaymentMethod | str,
    ) -> PaymentOrder:
        if isinstance(payment_method, str):
            try:
                payment_method = PaymentMethod(payment_method)
            except ValueError:
                raise ValueError("不支持的支付方式")

        stmt = select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("订单不存在")

        if order.status == PaymentStatus.PAID.value:
            return order

        if order.status not in (PaymentStatus.PENDING.value,):
            raise ValueError("订单状态不允许支付")

        if order.expires_at:
            now = datetime.now(timezone.utc)
            expires_at = order.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now > expires_at:
                raise ValueError("订单已过期")

        user_stmt = select(User).where(User.id == order.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError("用户不存在")

        if payment_method == PaymentMethod.BALANCE:
            balance_stmt = select(UserBalance).where(UserBalance.user_id == order.user_id)
            balance_result = await db.execute(balance_stmt)
            user_balance = balance_result.scalar_one_or_none()
            if not user_balance:
                raise ValueError("用户余额账户不存在")
            if user_balance.balance < order.actual_amount:
                raise ValueError("余额不足")

            balance_before = user_balance.balance
            balance_after = balance_before - order.actual_amount
            user_balance.balance = balance_after
            user_balance.total_consumed = (user_balance.total_consumed or 0) + order.actual_amount

            transaction = BalanceTransaction(
                user_id=order.user_id,
                order_id=order.id,
                type="consume",
                amount=-order.actual_amount,
                balance_before=balance_before,
                balance_after=balance_after,
                description=f"支付订单 {order.order_no}",
            )
            db.add(transaction)

        order.status = PaymentStatus.PAID.value
        order.payment_method = payment_method.value
        order.paid_at = datetime.now(timezone.utc)
        order.trade_no = order.trade_no or f"TXN{uuid.uuid4().hex[:12].upper()}"

        if order.order_type == "consultation" and order.related_id:
            consult_stmt = select(LawyerConsultation).where(LawyerConsultation.id == order.related_id)
            consult_result = await db.execute(consult_stmt)
            consultation = consult_result.scalar_one_or_none()
            if consultation:
                consultation.status = "confirmed"

        await db.commit()
        await db.refresh(order)
        return order

    async def refund_payment(
        self,
        db: AsyncSession,
        order_no: str,
    ) -> PaymentOrder:
        stmt = select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("订单不存在")

        if order.status != PaymentStatus.PAID.value:
            raise ValueError("订单未支付或已退款")

        balance_stmt = select(UserBalance).where(UserBalance.user_id == order.user_id)
        balance_result = await db.execute(balance_stmt)
        user_balance = balance_result.scalar_one_or_none()
        if not user_balance:
            raise ValueError("用户余额不存在")

        if user_balance.balance < order.actual_amount:
            raise ValueError("退款失败：用户余额不足")

        balance_before = user_balance.balance
        balance_after = balance_before + order.actual_amount
        user_balance.balance = balance_after

        transaction = BalanceTransaction(
            user_id=order.user_id,
            order_id=order.id,
            type="refund",
            amount=order.actual_amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=f"退款订单 {order.order_no}",
        )
        db.add(transaction)

        order.status = PaymentStatus.REFUNDED.value
        await db.commit()
        await db.refresh(order)
        return order

    async def get_order(self, db: AsyncSession, order_no: str) -> PaymentOrder | None:
        stmt = select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_orders(self, db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10, status_filter: str | None = None) -> tuple[list, int]:
        from sqlalchemy import func
        conditions = [PaymentOrder.user_id == user_id]
        if status_filter:
            conditions.append(PaymentOrder.status == status_filter)
        count_stmt = select(func.count()).select_from(PaymentOrder).where(*conditions)
        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = select(PaymentOrder).where(*conditions).order_by(PaymentOrder.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        orders = (await db.execute(stmt)).scalars().all()
        return orders, total

    async def cancel_order(self, db: AsyncSession, order_no: str, user_id: int) -> PaymentOrder:
        stmt = select(PaymentOrder).where(PaymentOrder.order_no == order_no, PaymentOrder.user_id == user_id)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("订单不存在")
        if order.status != PaymentStatus.PENDING.value:
            raise ValueError("订单状态不允许取消")
        order.status = PaymentStatus.CANCELLED.value
        await db.commit()
        await db.refresh(order)
        return order

    async def get_user_balance(self, db: AsyncSession, user_id: int) -> UserBalance:
        stmt = select(UserBalance).where(UserBalance.user_id == user_id)
        result = await db.execute(stmt)
        balance = result.scalar_one_or_none()
        if not balance:
            balance = UserBalance(user_id=user_id, balance=0.0, frozen=0.0)
            db.add(balance)
            await db.commit()
            await db.refresh(balance)
        return balance

    async def get_balance_transactions(self, db: AsyncSession, user_id: int, page: int = 1, page_size: int = 10) -> tuple[list, int]:
        from sqlalchemy import func
        conditions = [BalanceTransaction.user_id == user_id]
        count_stmt = select(func.count()).select_from(BalanceTransaction).where(*conditions)
        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = select(BalanceTransaction).where(*conditions).order_by(BalanceTransaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        transactions = (await db.execute(stmt)).scalars().all()
        return transactions, total

    async def mark_order_paid(self, db: AsyncSession, order_no: str, payment_method: str = "alipay", trade_no: str | None = None) -> PaymentOrder:
        valid_methods = {"alipay", "wechat", "balance", "ikunpay"}
        if payment_method not in valid_methods:
            raise ValueError("无效的支付方式")
        stmt = select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("订单不存在")
        if order.status == PaymentStatus.PAID.value:
            return order
        if order.order_type != OrderType.RECHARGE.value and order.order_type != "recharge":
            raise ValueError("仅充值订单支持该操作")
        order.status = PaymentStatus.PAID.value
        order.payment_method = payment_method
        order.paid_at = datetime.now(timezone.utc)
        order.trade_no = trade_no or order.trade_no or f"TXN{uuid.uuid4().hex[:12].upper()}"

        event = PaymentCallbackEvent(
            provider=payment_method,
            order_no=order_no,
            trade_no=order.trade_no,
            amount=order.actual_amount,
            verified=True,
            raw_payload="{}",
        )
        db.add(event)

        if order.order_type == OrderType.RECHARGE.value or order.order_type == "recharge":
            balance_stmt = select(UserBalance).where(UserBalance.user_id == order.user_id)
            balance_result = await db.execute(balance_stmt)
            user_balance = balance_result.scalar_one_or_none()
            if not user_balance:
                user_balance = UserBalance(
                    user_id=order.user_id,
                    balance=order.actual_amount,
                    total_recharged=order.actual_amount,
                )
                db.add(user_balance)
            else:
                user_balance.balance = user_balance.balance + order.actual_amount
                user_balance.total_recharged = user_balance.total_recharged + order.actual_amount

        await db.commit()
        await db.refresh(order)
        return order

    async def admin_get_orders(self, db: AsyncSession, page: int = 1, page_size: int = 10, status_filter: str | None = None, user_id: int | None = None) -> tuple[list, int]:
        from sqlalchemy import func
        conditions = []
        if status_filter:
            conditions.append(PaymentOrder.status == status_filter)
        if user_id:
            conditions.append(PaymentOrder.user_id == user_id)
        count_stmt = select(func.count()).select_from(PaymentOrder).where(*conditions)
        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = select(PaymentOrder).where(*conditions).order_by(PaymentOrder.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        orders = (await db.execute(stmt)).scalars().all()
        return orders, total

    async def admin_refund(self, db: AsyncSession, order_no: str) -> PaymentOrder:
        stmt = select(PaymentOrder).where(PaymentOrder.order_no == order_no)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError("订单不存在")
        if order.status == PaymentStatus.REFUNDED.value:
            return order
        if order.status != PaymentStatus.PAID.value:
            raise ValueError("只能退款已支付订单")

        balance_stmt = select(UserBalance).where(UserBalance.user_id == order.user_id)
        balance_result = await db.execute(balance_stmt)
        user_balance = balance_result.scalar_one_or_none()
        if user_balance:
            user_balance.balance = user_balance.balance + order.actual_amount

        transaction = BalanceTransaction(
            user_id=order.user_id,
            order_id=order.id,
            type="refund",
            amount=order.actual_amount,
            balance_before=user_balance.balance - order.actual_amount if user_balance else order.actual_amount,
            balance_after=user_balance.balance if user_balance else order.actual_amount,
            description=f"退款订单 {order.order_no}",
        )
        db.add(transaction)

        order.status = PaymentStatus.REFUNDED.value
        await db.commit()
        await db.refresh(order)
        return order

    async def get_callback_events(self, db: AsyncSession, page: int = 1, page_size: int = 10, order_no: str | None = None, verified: bool | None = None, provider: str | None = None, has_error: bool | None = None) -> tuple[list, int]:
        from sqlalchemy import func, or_
        conditions = []
        if order_no:
            conditions.append(PaymentCallbackEvent.order_no == order_no)
        if verified is not None:
            conditions.append(PaymentCallbackEvent.verified == verified)
        if provider:
            conditions.append(PaymentCallbackEvent.provider == provider)
        if has_error is True:
            conditions.append(PaymentCallbackEvent.error_message != None)
            conditions.append(PaymentCallbackEvent.error_message != "")
        elif has_error is False:
            conditions.append(or_(PaymentCallbackEvent.error_message == None, PaymentCallbackEvent.error_message == ""))
        count_stmt = select(func.count()).select_from(PaymentCallbackEvent).where(*conditions)
        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = select(PaymentCallbackEvent).where(*conditions).order_by(PaymentCallbackEvent.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        events = (await db.execute(stmt)).scalars().all()
        return events, total

    async def get_pricing(self, db: AsyncSession) -> dict:
        from app.models.system import SystemConfig
        pricing: dict = {"vip": {}, "services": {}, "packs": {"ai_chat": [], "document_generate": []}}

        _DEFAULT_AI_PACKS = {10: 12.0, 50: 49.0, 100: 99.0}
        _DEFAULT_DOC_PACKS = {5: 9.9, 20: 29.9, 50: 59.9}

        vip_days = (await db.execute(select(SystemConfig.value).where(SystemConfig.key == "vip_days"))).scalar_one_or_none()
        vip_price = (await db.execute(select(SystemConfig.value).where(SystemConfig.key == "vip_price"))).scalar_one_or_none()
        if vip_days and vip_price:
            pricing["vip"] = {"days": int(vip_days), "price": float(vip_price)}

        lcr_price = (await db.execute(select(SystemConfig.value).where(SystemConfig.key == "light_consult_review_price"))).scalar_one_or_none()
        if lcr_price:
            pricing["services"]["light_consult_review"] = {"price": float(lcr_price)}

        for count, default_price in sorted(_DEFAULT_AI_PACKS.items()):
            price_val = (await db.execute(select(SystemConfig.value).where(SystemConfig.key == f"ai_chat_pack_{count}_price"))).scalar_one_or_none()
            pricing["packs"]["ai_chat"].append({"count": count, "price": float(price_val) if price_val else default_price})

        for count, default_price in sorted(_DEFAULT_DOC_PACKS.items()):
            price_val = (await db.execute(select(SystemConfig.value).where(SystemConfig.key == f"doc_pack_{count}_price"))).scalar_one_or_none()
            if not price_val:
                price_val = (await db.execute(select(SystemConfig.value).where(SystemConfig.key == f"document_pack_{count}_price"))).scalar_one_or_none()
            pricing["packs"]["document_generate"].append({"count": count, "price": float(price_val) if price_val else default_price})

        pack_options_json = (await db.execute(select(SystemConfig.value).where(SystemConfig.key == "AI_CHAT_PACK_OPTIONS_JSON"))).scalar_one_or_none()
        if pack_options_json:
            import json
            try:
                pack_options = json.loads(pack_options_json)
                for count_str, price in sorted(pack_options.items(), key=lambda x: int(x[0])):
                    existing = [p for p in pricing["packs"]["ai_chat"] if p["count"] == int(count_str)]
                    if not existing:
                        pricing["packs"]["ai_chat"].append({"count": int(count_str), "price": float(price)})
            except (json.JSONDecodeError, ValueError):
                pass
        pricing["packs"]["ai_chat"].sort(key=lambda x: x["count"])

        return pricing


payment_service = PaymentService()
