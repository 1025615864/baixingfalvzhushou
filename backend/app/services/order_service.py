from __future__ import annotations

import random
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.payment import PaymentOrder, PaymentStatus, BalanceTransaction, UserBalance


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_dict(self, order: PaymentOrder) -> dict:
        return {
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "order_type": order.order_type,
            "amount": order.amount,
            "actual_amount": order.actual_amount,
            "status": order.status,
            "payment_method": order.payment_method,
            "related_id": order.related_id,
            "related_type": order.related_type,
            "trade_no": order.trade_no,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "title": order.title,
            "description": order.description,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            "expires_at": order.expires_at.isoformat() if order.expires_at else None,
        }

    async def list_orders(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        keyword: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        conditions = [PaymentOrder.user_id == user_id]

        if status:
            conditions.append(PaymentOrder.status == status)

        if keyword:
            kw = f"%{keyword}%"
            conditions.append(
                (PaymentOrder.order_no.ilike(kw))
                | (PaymentOrder.title.ilike(kw))
            )

        if date_from:
            try:
                dt_from = datetime.fromisoformat(date_from)
                conditions.append(PaymentOrder.created_at >= dt_from)
            except ValueError:
                pass

        if date_to:
            try:
                dt_to = datetime.fromisoformat(date_to)
                conditions.append(PaymentOrder.created_at <= dt_to)
            except ValueError:
                pass

        count_stmt = select(func.count()).select_from(PaymentOrder).where(*conditions)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(PaymentOrder)
            .where(*conditions)
            .order_by(PaymentOrder.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        orders = result.scalars().all()

        items = [
            {
                "id": o.id,
                "order_no": o.order_no,
                "order_type": o.order_type,
                "title": o.title,
                "amount": o.amount,
                "status": o.status,
                "payment_method": o.payment_method,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total + page_size - 1) // page_size),
        }

    async def get_order_detail(self, user_id: int, order_id: int) -> dict:
        stmt = select(PaymentOrder).where(
            PaymentOrder.id == order_id, PaymentOrder.user_id == user_id
        )
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        order_dict = self._to_dict(order)

        timeline = []
        timeline.append(
            {"time": order.created_at.isoformat() if order.created_at else None, "event": "订单创建"}
        )
        if order.status == PaymentStatus.PAID.value and order.paid_at:
            timeline.append(
                {"time": order.paid_at.isoformat(), "event": "支付成功"}
            )
        if order.status == PaymentStatus.CANCELLED.value:
            timeline.append(
                {"time": order.updated_at.isoformat() if order.updated_at else None, "event": "订单已取消"}
            )
        if order.status == PaymentStatus.REFUNDED.value:
            timeline.append(
                {"time": order.updated_at.isoformat() if order.updated_at else None, "event": "已退款"}
            )

        payment_info = {
            "amount": order.amount,
            "actual_amount": order.actual_amount,
            "payment_method": order.payment_method,
            "payment_status": order.status,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
            "trade_no": order.trade_no,
        }

        return {
            "order": order_dict,
            "service_details": {
                "related_id": order.related_id,
                "related_type": order.related_type,
                "description": order.description,
            },
            "payment_info": payment_info,
            "timeline": timeline,
        }

    async def create_order(self, user_id: int, data: dict) -> dict:
        amount = data.get("amount", 0)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="金额必须大于0")

        valid_types = {"consultation", "document_review", "litigation", "membership", "service", "vip", "recharge", "light_consult_review"}
        order_type = data.get("service_type", data.get("order_type", ""))
        if order_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"无效的服务类型: {order_type}")

        order_no = f"ORD{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"

        order = PaymentOrder(
            order_no=order_no,
            user_id=user_id,
            order_type=order_type,
            amount=amount,
            actual_amount=amount,
            status=PaymentStatus.PENDING.value,
            title=data.get("service_name", data.get("title", "支付订单")),
            description=data.get("note"),
            related_id=data.get("service_id", data.get("related_id")),
            related_type=data.get("related_type"),
            payment_method=data.get("payment_method"),
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        return {
            "id": order.id,
            "order_no": order.order_no,
            "amount": order.amount,
            "payment_status": order.status,
            "order_status": order.status,
            "payment_url": f"https://pay.baixingfalv.com/order/{order.order_no}",
            "created_at": order.created_at.isoformat() if order.created_at else None,
        }

    async def pay_order(self, user_id: int, order_id: int, payment_method: str) -> dict:
        valid_methods = {"wechat", "alipay", "balance"}
        if payment_method not in valid_methods:
            raise HTTPException(status_code=400, detail="不支持的支付方式，可选: wechat, alipay, balance")

        stmt = select(PaymentOrder).where(
            PaymentOrder.id == order_id, PaymentOrder.user_id == user_id
        )
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        if order.status != PaymentStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="订单当前状态不可支付")

        if payment_method == "balance":
            balance_stmt = select(UserBalance).where(UserBalance.user_id == user_id)
            balance_result = await self.db.execute(balance_stmt)
            user_balance = balance_result.scalar_one_or_none()
            if not user_balance or user_balance.balance < order.actual_amount:
                raise HTTPException(status_code=400, detail="余额不足")

            balance_before = user_balance.balance
            balance_after = balance_before - order.actual_amount
            user_balance.balance = balance_after
            user_balance.total_consumed = (user_balance.total_consumed or 0) + order.actual_amount

            transaction = BalanceTransaction(
                user_id=user_id,
                order_id=order.id,
                type="consume",
                amount=-order.actual_amount,
                balance_before=balance_before,
                balance_after=balance_after,
                description=f"支付订单 {order.order_no}",
            )
            self.db.add(transaction)

        now = datetime.now(timezone.utc)
        order.status = PaymentStatus.PAID.value
        order.payment_method = payment_method
        order.paid_at = now
        order.trade_no = f"TRADE{now.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"

        await self.db.commit()
        await self.db.refresh(order)

        return {
            "success": True,
            "message": "支付成功",
            "order_no": order.order_no,
            "trade_no": order.trade_no,
            "amount": order.actual_amount,
            "payment_method": payment_method,
            "payment_status": PaymentStatus.PAID.value,
            "order_status": PaymentStatus.PAID.value,
            "paid_at": now.isoformat(),
        }

    async def cancel_order(self, user_id: int, order_id: int, reason: str | None = None) -> dict:
        stmt = select(PaymentOrder).where(
            PaymentOrder.id == order_id, PaymentOrder.user_id == user_id
        )
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        if order.status != PaymentStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="只有待支付状态的订单才能取消")

        order.status = PaymentStatus.CANCELLED.value
        order.description = (order.description or "") + (f" | 取消原因: {reason}" if reason else " | 用户取消")

        await self.db.commit()
        await self.db.refresh(order)

        return {
            "success": True,
            "message": "订单已取消",
            "order_no": order.order_no,
            "order_status": PaymentStatus.CANCELLED.value,
        }

    async def get_order_stats(self, user_id: int) -> dict:
        base_cond = PaymentOrder.user_id == user_id

        total_stmt = select(func.count()).select_from(PaymentOrder).where(base_cond)
        total_orders = (await self.db.execute(total_stmt)).scalar() or 0

        amount_stmt = select(func.coalesce(func.sum(PaymentOrder.amount), 0)).where(base_cond)
        total_amount = (await self.db.execute(amount_stmt)).scalar() or 0

        status_stmt = (
            select(PaymentOrder.status, func.count().label("cnt"))
            .where(base_cond)
            .group_by(PaymentOrder.status)
        )
        status_result = await self.db.execute(status_stmt)
        by_status = {row.status: row.cnt for row in status_result}

        type_stmt = (
            select(PaymentOrder.order_type, func.count().label("cnt"))
            .where(base_cond)
            .group_by(PaymentOrder.order_type)
        )
        type_result = await self.db.execute(type_stmt)
        by_service_type = {row.order_type: row.cnt for row in type_result}

        monthly_stmt = (
            select(
                func.strftime("%Y-%m", PaymentOrder.created_at).label("month"),
                func.count().label("orders"),
                func.coalesce(func.sum(PaymentOrder.amount), 0).label("amount"),
            )
            .where(base_cond)
            .group_by("month")
            .order_by("month")
        )
        monthly_result = await self.db.execute(monthly_stmt)
        monthly_trend = [
            {"month": row.month, "orders": row.orders, "amount": round(float(row.amount), 2)}
            for row in monthly_result
        ]

        return {
            "total_orders": total_orders,
            "total_amount": round(float(total_amount), 2),
            "by_status": by_status,
            "by_service_type": by_service_type,
            "monthly_trend": monthly_trend,
        }
