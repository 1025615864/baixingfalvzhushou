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