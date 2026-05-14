"""订单服务 - 服务层"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, OrderType, PaymentMethod


class OrderService:
    """订单服务"""

    async def create_order(
        self,
        session: AsyncSession,
        user_id: int,
        order_type: OrderType,
        title: str,
        amount: float,
        description: str = None,
        business_id: int = None,
        business_type: str = None,
        discount_amount: float = 0,
    ) -> Order:
        """创建订单"""
        order_no = self._generate_order_no()
        actual_amount = amount - discount_amount

        order = Order(
            order_no=order_no,
            user_id=user_id,
            order_type=order_type,
            title=title,
            description=description,
            amount=amount,
            discount_amount=discount_amount,
            actual_amount=actual_amount,
            status=OrderStatus.PENDING,
            business_id=business_id,
            business_type=business_type,
        )

        session.add(order)
        await session.flush()
        return order

    async def get_order(
        self,
        session: AsyncSession,
        order_id: int,
        user_id: int = None,
    ) -> Optional[Order]:
        """获取订单"""
        stmt = select(Order).where(Order.id == order_id)
        if user_id:
            stmt = stmt.where(Order.user_id == user_id)

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_order_by_no(
        self,
        session: AsyncSession,
        order_no: str,
        user_id: int = None,
    ) -> Optional[Order]:
        """通过订单号获取订单"""
        stmt = select(Order).where(Order.order_no == order_no)
        if user_id:
            stmt = stmt.where(Order.user_id == user_id)

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_orders(
        self,
        session: AsyncSession,
        user_id: int,
        status: OrderStatus = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Order], int]:
        """获取用户订单列表"""
        base_filter = [Order.user_id == user_id]
        if status:
            base_filter.append(Order.status == status)

        count_stmt = select(func.count(Order.id)).where(*base_filter)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = select(Order).where(*base_filter).order_by(Order.created_at.desc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        orders = result.scalars().all()

        return list(orders), total

    async def pay_order(
        self,
        session: AsyncSession,
        order_no: str,
        payment_method: PaymentMethod,
        saga_id: str = None,
    ) -> Order:
        """支付订单"""
        stmt = (
            update(Order)
            .where(Order.order_no == order_no, Order.status == OrderStatus.PENDING)
            .values(
                status=OrderStatus.PAID,
                payment_method=payment_method,
                payment_time=datetime.now(timezone.utc),
                paid_at=datetime.now(timezone.utc),
                saga_id=saga_id,
            )
            .returning(Order)
        )

        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order {order_no} not found or not in PENDING status")

        return order

    async def cancel_order(
        self,
        session: AsyncSession,
        order_no: str,
        reason: str = None,
    ) -> Order:
        """取消订单"""
        stmt = (
            update(Order)
            .where(Order.order_no == order_no, Order.status == OrderStatus.PENDING)
            .values(
                status=OrderStatus.CANCELLED,
                cancel_reason=reason,
                cancelled_at=datetime.now(timezone.utc),
            )
            .returning(Order)
        )

        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order {order_no} not found or not in PENDING status")

        return order

    async def complete_order(
        self,
        session: AsyncSession,
        order_no: str,
    ) -> Order:
        """完成订单"""
        stmt = (
            update(Order)
            .where(Order.order_no == order_no, Order.status == OrderStatus.PAID)
            .values(
                status=OrderStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )
            .returning(Order)
        )

        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order {order_no} not found or not in PAID status")

        return order

    async def refund_order(
        self,
        session: AsyncSession,
        order_no: str,
        reason: str = None,
    ) -> Order:
        """退款订单"""
        stmt = (
            update(Order)
            .where(Order.order_no == order_no)
            .values(
                status=OrderStatus.REFUNDED,
                refund_reason=reason,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(Order)
        )

        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order {order_no} not found")

        return order

    async def update_saga_status(
        self,
        session: AsyncSession,
        saga_id: str,
        saga_status: str,
    ) -> int:
        """更新 Saga 状态"""
        stmt = (
            update(Order)
            .where(Order.saga_id == saga_id)
            .values(saga_status=saga_status, updated_at=datetime.now(timezone.utc))
        )

        result = await session.execute(stmt)
        return result.rowcount

    async def auto_cancel_expired_orders(
        self,
        session: AsyncSession,
        timeout_minutes: int = 30,
    ) -> int:
        """自动取消超时未支付的订单"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        stmt = (
            update(Order)
            .where(
                Order.status == OrderStatus.PENDING,
                Order.created_at < cutoff_time,
            )
            .values(
                status=OrderStatus.CANCELLED,
                cancel_reason=f"订单超时未支付，自动取消（超时{timeout_minutes}分钟）",
                cancelled_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await session.execute(stmt)
        return result.rowcount

    async def get_order_stats(
        self,
        session: AsyncSession,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """获取订单统计信息"""
        base_filter = [
            Order.created_at >= start_date,
            Order.created_at <= end_date,
        ]

        total_stmt = select(func.count(Order.id)).where(*base_filter)
        total_result = await session.execute(total_stmt)
        total_orders = total_result.scalar_one()

        revenue_stmt = select(func.coalesce(func.sum(Order.actual_amount), 0)).where(
            *base_filter,
            Order.status.in_([OrderStatus.PAID, OrderStatus.COMPLETED]),
        )
        revenue_result = await session.execute(revenue_stmt)
        total_revenue = float(revenue_result.scalar_one())

        status_stmt = (
            select(Order.status, func.count(Order.id))
            .where(*base_filter)
            .group_by(Order.status)
        )
        status_result = await session.execute(status_stmt)
        orders_by_status = {str(status.value): count for status, count in status_result.all()}

        type_stmt = (
            select(Order.order_type, func.count(Order.id))
            .where(*base_filter)
            .group_by(Order.order_type)
        )
        type_result = await session.execute(type_stmt)
        orders_by_type = {str(otype.value): count for otype, count in type_result.all()}

        daily_stmt = (
            select(cast(Order.created_at, Date).label("date"), func.count(Order.id))
            .where(*base_filter)
            .group_by(cast(Order.created_at, Date))
            .order_by(cast(Order.created_at, Date))
        )
        daily_result = await session.execute(daily_stmt)
        daily_counts = [
            {"date": date.isoformat(), "count": count}
            for date, count in daily_result.all()
        ]

        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "orders_by_status": orders_by_status,
            "orders_by_type": orders_by_type,
            "daily_counts": daily_counts,
        }

    async def list_all_orders(
        self,
        session: AsyncSession,
        user_id: int = None,
        order_type: OrderType = None,
        status: OrderStatus = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Order], int]:
        """管理员获取所有订单列表"""
        base_filter = []
        if user_id:
            base_filter.append(Order.user_id == user_id)
        if order_type:
            base_filter.append(Order.order_type == order_type)
        if status:
            base_filter.append(Order.status == status)

        count_stmt = select(func.count(Order.id)).where(*base_filter)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(Order)
            .where(*base_filter)
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        orders = result.scalars().all()

        return list(orders), total

    async def force_cancel_order(
        self,
        session: AsyncSession,
        order_no: str,
        reason: str = None,
    ) -> Order:
        """强制取消订单（管理员，不受状态限制）"""
        stmt = (
            update(Order)
            .where(Order.order_no == order_no)
            .values(
                status=OrderStatus.CANCELLED,
                cancel_reason=reason or "管理员强制取消",
                cancelled_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            .returning(Order)
        )
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError(f"Order {order_no} not found")

        return order

    @staticmethod
    def _generate_order_no() -> str:
        """生成订单号"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        uuid_short = uuid.uuid4().hex[:8]
        return f"ORD{timestamp}{uuid_short}"


order_service = OrderService()
