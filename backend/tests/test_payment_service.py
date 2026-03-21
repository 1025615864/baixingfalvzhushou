"""
支付服务单元测试

测试覆盖：
- 订单创建
- 支付处理
- 退款处理
- 边界场景和异常情况
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock, AsyncMock

from app.services.payment_service import PaymentService, payment_service
from app.models.payment import (
    PaymentOrder,
    PaymentStatus,
    PaymentMethod,
    UserBalance,
    BalanceTransaction,
)
from app.models.lawfirm import LawyerConsultation


@pytest.mark.asyncio
async def test_create_order_success(db: AsyncSession):
    """测试成功创建订单"""
    # Arrange
    service = PaymentService()
    user_id = 1
    amount = 100.0
    order_type = "consultation"
    title = "法律咨询订单"
    description = "咨询订单描述"

    # Act
    order = await service.create_order(
        db,
        user_id=user_id,
        amount=amount,
        order_type=order_type,
        title=title,
        description=description,
    )

    # Assert
    assert order is not None
    assert order.user_id == user_id
    assert order.amount == amount
    assert order.actual_amount == amount
    assert order.order_type == order_type
    assert order.status == PaymentStatus.PENDING
    assert order.title == title
    assert order.description == description
    assert order.order_no is not None
    assert len(order.order_no) > 0


@pytest.mark.asyncio
async def test_create_order_without_title(db: AsyncSession):
    """测试创建订单时使用默认标题"""
    # Arrange
    service = PaymentService()
    user_id = 1
    amount = 50.0
    order_type = "service"

    # Act
    order = await service.create_order(
        db,
        user_id=user_id,
        amount=amount,
        order_type=order_type,
    )

    # Assert
    assert order is not None
    assert order.title == "支付订单"


@pytest.mark.asyncio
async def test_process_payment_with_balance_success(db: AsyncSession):
    """测试使用余额支付成功"""
    # Arrange
    service = PaymentService()
    
    # 创建用户余额记录
    user_balance = UserBalance(user_id=1, balance=200.0)
    db.add(user_balance)
    await db.commit()
    
    # 创建待支付订单
    order = PaymentOrder(
        order_no="TEST_ORDER_001",
        user_id=1,
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PENDING,
        title="测试订单",
    )
    db.add(order)
    await db.commit()

    # Act
    result = await service.process_payment(
        db,
        order_no="TEST_ORDER_001",
        payment_method=PaymentMethod.BALANCE,
    )

    # Assert
    assert result.status == PaymentStatus.PAID
    assert result.payment_method == PaymentMethod.BALANCE.value
    assert result.paid_at is not None
    
    # 验证余额已扣除
    balance_result = await db.execute(
        select(UserBalance).where(UserBalance.user_id == 1)
    )
    balance = balance_result.scalar_one()
    assert balance.balance == 100.0
    
    # 验证交易记录已创建
    transaction_result = await db.execute(
        select(BalanceTransaction).where(BalanceTransaction.order_id == order.id)
    )
    transaction = transaction_result.scalar_one()
    assert transaction is not None
    assert transaction.type == "consume"
    assert transaction.amount == -100.0
    assert transaction.balance_before == 200.0
    assert transaction.balance_after == 100.0


@pytest.mark.asyncio
async def test_process_payment_insufficient_balance(db: AsyncSession):
    """测试余额不足时支付失败"""
    # Arrange
    service = PaymentService()
    
    # 创建用户余额记录（余额不足）
    user_balance = UserBalance(user_id=1, balance=50.0)
    db.add(user_balance)
    await db.commit()
    
    # 创建待支付订单（金额100）
    order = PaymentOrder(
        order_no="TEST_ORDER_002",
        user_id=1,
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PENDING,
        title="测试订单",
    )
    db.add(order)
    await db.commit()

    # Act & Assert
    with pytest.raises(ValueError):
        await service.process_payment(
            db,
            order_no="TEST_ORDER_002",
            payment_method=PaymentMethod.BALANCE,
        )


@pytest.mark.asyncio
async def test_process_payment_order_not_found(db: AsyncSession):
    """测试处理不存在的订单"""
    # Arrange
    service = PaymentService()

    # Act & Assert
    with pytest.raises(ValueError, match="订单不存在"):
        await service.process_payment(
            db,
            order_no="NONEXISTENT_ORDER",
            payment_method=PaymentMethod.BALANCE,
        )


@pytest.mark.asyncio
async def test_process_payment_already_paid(db: AsyncSession):
    """测试处理已支付的订单"""
    # Arrange
    service = PaymentService()
    
    # 创建已支付订单
    order = PaymentOrder(
        order_no="TEST_ORDER_003",
        user_id=1,
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PAID,
        payment_method=PaymentMethod.BALANCE,
        paid_at=datetime.now(timezone.utc),
        title="已支付订单",
    )
    db.add(order)
    await db.commit()

    # Act
    result = await service.process_payment(
        db,
        order_no="TEST_ORDER_003",
        payment_method=PaymentMethod.BALANCE,
    )

    # Assert - 应该直接返回已支付订单，不报错
    assert result.status == PaymentStatus.PAID


@pytest.mark.asyncio
async def test_process_payment_with_consultation_update(db: AsyncSession):
    """测试支付咨询订单时更新咨询状态"""
    # Arrange
    service = PaymentService()
    
    # 创建用户余额记录
    user_balance = UserBalance(user_id=1, balance=200.0)
    db.add(user_balance)
    
    # 创建待处理的咨询
    consultation = LawyerConsultation(
        lawyer_id=1,
        user_id=1,
        status="pending",
        subject="测试问题",
    )
    db.add(consultation)
    await db.commit()
    await db.refresh(consultation)
    
    # 创建关联咨询的订单
    order = PaymentOrder(
        order_no="TEST_ORDER_004",
        user_id=1,
        order_type="consultation",
        related_id=consultation.id,
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PENDING,
        title="咨询订单",
    )
    db.add(order)
    await db.commit()

    # Act
    result = await service.process_payment(
        db,
        order_no="TEST_ORDER_004",
        payment_method=PaymentMethod.BALANCE,
    )

    # Assert
    assert result.status == PaymentStatus.PAID
    
    # 验证咨询状态已更新
    consultation_result = await db.execute(
        select(LawyerConsultation).where(LawyerConsultation.id == consultation.id)
    )
    updated_consultation = consultation_result.scalar_one()
    assert updated_consultation.status == "confirmed"


@pytest.mark.asyncio
async def test_process_payment_without_consultation_update(db: AsyncSession):
    """测试支付非咨询订单时不影响咨询"""
    # Arrange
    service = PaymentService()
    
    # 创建用户余额记录
    user_balance = UserBalance(user_id=1, balance=200.0)
    db.add(user_balance)
    
    # 创建非咨询订单（无related_id）
    order = PaymentOrder(
        order_no="TEST_ORDER_005",
        user_id=1,
        order_type="service",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PENDING,
        title="服务订单",
    )
    db.add(order)
    await db.commit()

    # Act
    result = await service.process_payment(
        db,
        order_no="TEST_ORDER_005",
        payment_method=PaymentMethod.BALANCE,
    )

    # Assert
    assert result.status == PaymentStatus.PAID


@pytest.mark.asyncio
async def test_refund_payment_success(db: AsyncSession):
    """测试退款成功"""
    # Arrange
    service = PaymentService()
    
    # 创建用户余额记录
    user_balance = UserBalance(user_id=1, balance=100.0)
    db.add(user_balance)
    
    # 创建已支付订单
    order = PaymentOrder(
        order_no="TEST_ORDER_006",
        user_id=1,
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PAID,
        paid_at=datetime.now(timezone.utc),
        title="待退款订单",
    )
    db.add(order)
    await db.commit()

    # Act
    result = await service.refund_payment(
        db,
        order_no="TEST_ORDER_006",
    )

    # Assert
    assert result.status == PaymentStatus.REFUNDED
    
    # 验证余额已增加
    balance_result = await db.execute(
        select(UserBalance).where(UserBalance.user_id == 1)
    )
    balance = balance_result.scalar_one()
    assert balance.balance == 200.0
    
    # 验证退款交易记录已创建
    transaction_result = await db.execute(
        select(BalanceTransaction).where(BalanceTransaction.order_id == order.id)
    )
    transaction = transaction_result.scalar_one()
    assert transaction is not None
    assert transaction.type == "refund"
    assert transaction.amount == 100.0
    assert transaction.balance_before == 100.0
    assert transaction.balance_after == 200.0


@pytest.mark.asyncio
async def test_refund_payment_order_not_found(db: AsyncSession):
    """测试退款不存在的订单"""
    # Arrange
    service = PaymentService()

    # Act & Assert
    with pytest.raises(ValueError, match="订单不存在"):
        await service.refund_payment(
            db,
            order_no="NONEXISTENT_ORDER",
        )


@pytest.mark.asyncio
async def test_refund_payment_not_paid(db: AsyncSession):
    """测试退款未支付订单时失败"""
    # Arrange
    service = PaymentService()
    
    # 创建用户余额记录
    user_balance = UserBalance(user_id=1, balance=100.0)
    db.add(user_balance)
    
    # 创建待支付订单
    order = PaymentOrder(
        order_no="TEST_ORDER_007",
        user_id=1,
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PENDING,
        title="待支付订单",
    )
    db.add(order)
    await db.commit()

    # Act & Assert
    with pytest.raises(ValueError, match="订单未支付或已退款"):
        await service.refund_payment(
            db,
            order_no="TEST_ORDER_007",
        )


@pytest.mark.asyncio
async def test_refund_payment_already_refunded(db: AsyncSession):
    """测试退款已退款订单时失败"""
    # Arrange
    service = PaymentService()
    
    # 创建用户余额记录
    user_balance = UserBalance(user_id=1, balance=100.0)
    db.add(user_balance)
    
    # 创建已退款订单
    order = PaymentOrder(
        order_no="TEST_ORDER_008",
        user_id=1,
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.REFUNDED,
        title="已退款订单",
    )
    db.add(order)
    await db.commit()

    # Act & Assert
    with pytest.raises(ValueError, match="订单未支付或已退款"):
        await service.refund_payment(
            db,
            order_no="TEST_ORDER_008",
        )


@pytest.mark.asyncio
async def test_refund_payment_user_balance_not_exist(db: AsyncSession):
    """测试退款时用户余额不存在时失败"""
    # Arrange
    service = PaymentService()
    
    # 创建已支付订单（但没有用户余额记录）
    order = PaymentOrder(
        order_no="TEST_ORDER_009",
        user_id=1,
        order_type="consultation",
        amount=100.0,
        actual_amount=100.0,
        status=PaymentStatus.PAID,
        paid_at=datetime.now(timezone.utc),
        title="待退款订单",
    )
    db.add(order)
    await db.commit()

    # Act & Assert
    with pytest.raises(ValueError, match="用户余额不存在"):
        await service.refund_payment(
            db,
            order_no="TEST_ORDER_009",
        )


@pytest.mark.asyncio
async def test_payment_service_singleton():
    """测试支付服务单例"""
    # Act & Assert
    assert payment_service is not None
    assert isinstance(payment_service, PaymentService)


class TestPaymentExceptionHandling:
    """支付异常处理测试类"""

    @pytest.mark.asyncio
    async def test_process_payment_invalid_payment_method(self, db: AsyncSession):
        """测试处理无效支付方式"""
        # Arrange
        service = PaymentService()
        
        # 创建用户余额记录
        user_balance = UserBalance(user_id=1, balance=200.0)
        db.add(user_balance)
        await db.commit()
        
        # 创建待支付订单
        order = PaymentOrder(
            order_no="TEST_ORDER_EXCEPTION_001",
            user_id=1,
            order_type="consultation",
            amount=100.0,
            actual_amount=100.0,
            status=PaymentStatus.PENDING,
            title="测试订单",
        )
        db.add(order)
        await db.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="不支持的支付方式"):
            await service.process_payment(
                db,
                order_no="TEST_ORDER_EXCEPTION_001",
                payment_method="invalid_method",
            )

    @pytest.mark.asyncio
    async def test_process_payment_order_cancelled(self, db: AsyncSession):
        """测试处理已取消的订单"""
        # Arrange
        service = PaymentService()
        
        # 创建已取消订单
        order = PaymentOrder(
            order_no="TEST_ORDER_EXCEPTION_002",
            user_id=1,
            order_type="consultation",
            amount=100.0,
            actual_amount=100.0,
            status=PaymentStatus.CANCELLED,
            title="已取消订单",
        )
        db.add(order)
        await db.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="订单状态不允许支付"):
            await service.process_payment(
                db,
                order_no="TEST_ORDER_EXCEPTION_002",
                payment_method=PaymentMethod.BALANCE,
            )

    @pytest.mark.asyncio
    async def test_process_payment_order_expired(self, db: AsyncSession):
        """测试处理已过期的订单"""
        # Arrange
        service = PaymentService()
        
        from datetime import timedelta
        
        # 创建已过期订单
        order = PaymentOrder(
            order_no="TEST_ORDER_EXCEPTION_003",
            user_id=1,
            order_type="consultation",
            amount=100.0,
            actual_amount=100.0,
            status=PaymentStatus.PENDING,
            title="已过期订单",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(order)
        await db.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="订单已过期"):
            await service.process_payment(
                db,
                order_no="TEST_ORDER_EXCEPTION_003",
                payment_method=PaymentMethod.BALANCE,
            )

    @pytest.mark.asyncio
    async def test_refund_payment_insufficient_balance(self, db: AsyncSession):
        """测试退款时用户余额不足"""
        # Arrange
        service = PaymentService()
        
        # 创建用户余额记录（余额不足）
        user_balance = UserBalance(user_id=1, balance=50.0)  # 只有 50 元
        db.add(user_balance)
        
        # 创建已支付订单（100 元）
        order = PaymentOrder(
            order_no="TEST_ORDER_EXCEPTION_004",
            user_id=1,
            order_type="consultation",
            amount=100.0,
            actual_amount=100.0,
            status=PaymentStatus.PAID,
            paid_at=datetime.now(timezone.utc),
            title="待退款订单",
        )
        db.add(order)
        await db.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="退款失败：用户余额不足"):
            await service.refund_payment(
                db,
                order_no="TEST_ORDER_EXCEPTION_004",
            )


class TestPaymentErrorMessage:
    """支付错误消息测试类"""

    @pytest.mark.asyncio
    async def test_create_order_invalid_amount(self, db: AsyncSession):
        """测试创建订单时金额无效"""
        # Arrange
        service = PaymentService()

        # Act & Assert
        with pytest.raises(ValueError, match="订单金额必须大于 0"):
            await service.create_order(
                db,
                user_id=1,
                amount=0,
                order_type="consultation",
                title="测试订单",
            )

    @pytest.mark.asyncio
    async def test_create_order_negative_amount(self, db: AsyncSession):
        """测试创建订单时金额为负数"""
        # Arrange
        service = PaymentService()

        # Act & Assert
        with pytest.raises(ValueError, match="订单金额必须大于 0"):
            await service.create_order(
                db,
                user_id=1,
                amount=-100,
                order_type="consultation",
                title="测试订单",
            )

    @pytest.mark.asyncio
    async def test_process_payment_user_not_found(self, db: AsyncSession):
        """测试支付时用户不存在"""
        # Arrange
        service = PaymentService()
        
        # 创建待支付订单（用户不存在）
        order = PaymentOrder(
            order_no="TEST_ORDER_ERROR_001",
            user_id=999999,  # 不存在的用户 ID
            order_type="consultation",
            amount=100.0,
            actual_amount=100.0,
            status=PaymentStatus.PENDING,
            title="测试订单",
        )
        db.add(order)
        await db.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="用户不存在"):
            await service.process_payment(
                db,
                order_no="TEST_ORDER_ERROR_001",
                payment_method=PaymentMethod.BALANCE,
            )

    @pytest.mark.asyncio
    async def test_process_payment_balance_not_exist(self, db: AsyncSession):
        """测试支付时用户余额账户不存在"""
        # Arrange
        service = PaymentService()
        
        # 创建测试用户
        user = User(
            username="testuser_balance",
            email="balance@example.com",
            phone="13800138001",
            hashed_password="hashed_password",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # 创建待支付订单
        order = PaymentOrder(
            order_no="TEST_ORDER_ERROR_002",
            user_id=user.id,
            order_type="consultation",
            amount=100.0,
            actual_amount=100.0,
            status=PaymentStatus.PENDING,
            title="测试订单",
        )
        db.add(order)
        await db.commit()

        # Act & Assert
        with pytest.raises(ValueError, match="用户余额账户不存在"):
            await service.process_payment(
                db,
                order_no="TEST_ORDER_ERROR_002",
                payment_method=PaymentMethod.BALANCE,
            )


class TestPaymentConcurrency:
    """支付并发测试类"""

    @pytest.mark.asyncio
    async def test_process_payment_concurrent_requests(self, db: AsyncSession):
        """测试并发支付请求处理"""
        # Arrange
        service = PaymentService()
        
        # 创建用户余额记录
        user_balance = UserBalance(user_id=1, balance=500.0)
        db.add(user_balance)
        await db.commit()
        
        # 创建多个待支付订单
        order_nos = []
        for i in range(3):
            order = PaymentOrder(
                order_no=f"TEST_ORDER_CONCURRENT_{i:03d}",
                user_id=1,
                order_type="consultation",
                amount=100.0,
                actual_amount=100.0,
                status=PaymentStatus.PENDING,
                title=f"并发测试订单{i}",
            )
            db.add(order)
            order_nos.append(order.order_no)
        
        await db.commit()

        # Act - 并发执行支付
        import asyncio
        tasks = [
            service.process_payment(db, order_no=no, payment_method=PaymentMethod.BALANCE)
            for no in order_nos
        ]
        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 3
        for result in results:
            assert result.status == PaymentStatus.PAID
        
        # 验证最终余额
        balance_result = await db.execute(
            select(UserBalance).where(UserBalance.user_id == 1)
        )
        balance = balance_result.scalar_one()
        assert balance.balance == 200.0  # 500 - 300

    @pytest.mark.asyncio
    async def test_process_payment_race_condition(self, db: AsyncSession):
        """测试支付竞态条件处理"""
        # Arrange
        service = PaymentService()
        
        # 创建用户余额记录（刚好够支付一单）
        user_balance = UserBalance(user_id=1, balance=100.0)
        db.add(user_balance)
        
        # 创建两个待支付订单
        order1 = PaymentOrder(
            order_no="TEST_ORDER_RACE_001",
            user_id=1,
            order_type="consultation",
            amount=100.0,
            actual_amount=100.0,
            status=PaymentStatus.PENDING,
            title="竞态测试订单 1",
        )
        order2 = PaymentOrder(
            order_no="TEST_ORDER_RACE_002",
            user_id=1,
            order_type="consultation",
            amount=100.0,
            actual_amount=100.0,
            status=PaymentStatus.PENDING,
            title="竞态测试订单 2",
        )
        db.add(order1)
        db.add(order2)
        await db.commit()

        # Act - 尝试并发支付两个订单
        import asyncio
        
        async def try_payment(order_no):
            try:
                return await service.process_payment(
                    db, order_no=order_no, payment_method=PaymentMethod.BALANCE
                )
            except ValueError:
                return None
        
        tasks = [
            try_payment("TEST_ORDER_RACE_001"),
            try_payment("TEST_ORDER_RACE_002"),
        ]
        results = await asyncio.gather(*tasks)

        # Assert - 只有一个成功
        successful = [r for r in results if r is not None]
        assert len(successful) == 1