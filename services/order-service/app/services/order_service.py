"""订单服务 - 服务层"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
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
        stmt = select(Order).where(Order.user_id == user_id)
        if status:
            stmt = stmt.where(Order.status == status)

        count_stmt = select(Order).where(Order.user_id == user_id)
        if status:
            count_stmt = count_stmt.where(Order.status == status)

        count_result = await session.execute(count_stmt)
        total = len(count_result.scalars().all())

        stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
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
                payment_time=datetime.utcnow(),
                paid_at=datetime.utcnow(),
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
                cancelled_at=datetime.utcnow(),
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
                completed_at=datetime.utcnow(),
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
                updated_at=datetime.utcnow(),
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
            .values(saga_status=saga_status, updated_at=datetime.utcnow())
        )

        result = await session.execute(stmt)
        return result.rowcount

    @staticmethod
    def _generate_order_no() -> str:
        """生成订单号"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        uuid_short = uuid.uuid4().hex[:8]
        return f"ORD{timestamp}{uuid_short}"


order_service = OrderService()
