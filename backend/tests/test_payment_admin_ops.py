"""Payment Admin Operations Router Tests

Tests for admin order management, refunds, and callback event handling.
"""
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.payment import (
    PaymentOrder,
    PaymentCallbackEvent,
    PaymentStatus,
    UserBalance,
    BalanceTransaction,
)
from app.models.user import User
from app.utils.security import create_access_token
from tests.helpers.test_data_factory import UserFactory, OrderFactory


@pytest.mark.asyncio
async def test_admin_get_orders_empty(client: AsyncClient, db: AsyncSession):
    """Test admin order list when empty"""
    # Create admin user
    admin = await UserFactory.create_user(db, username="admin_test", role="admin")
    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    response = await client.get(
        "/api/payment/admin/orders",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_admin_get_orders_with_filters(client: AsyncClient, db: AsyncSession):
    """Test admin order list with status and user filters"""
    # Create admin and regular user
    admin = await UserFactory.create_user(db, username="admin_filter_test", role="admin")
    user = await UserFactory.create_user(db, username="user_filter_test")

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    # Create orders with different statuses
    order1 = await OrderFactory.create_order(db, user_id=user.id)
    order1.order_no = "ORD-001"
    order1.status = PaymentStatus.PENDING
    db.add(order1)
    await db.commit()
    
    order2 = await OrderFactory.create_order(db, user_id=user.id)
    order2.order_no = "ORD-002"
    order2.status = PaymentStatus.PAID
    db.add(order2)
    await db.commit()
    
    order3 = await OrderFactory.create_order(db, user_id=user.id)
    order3.order_no = "ORD-003"
    order3.status = PaymentStatus.PENDING
    db.add(order3)
    await db.commit()

    # Test status filter
    response = await client.get(
        "/api/payment/admin/orders?status_filter=pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["status"] == "pending"

    # Test user_id filter
    response = await client.get(
        f"/api/payment/admin/orders?user_id={user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_admin_refund_success(client: AsyncClient, db: AsyncSession):
    """Test successful refund of a paid order"""
    admin = await UserFactory.create_user(db, username="admin_refund_test", role="admin")
    user = await UserFactory.create_user(db, username="user_refund_test")

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    # Create a paid order
    order = PaymentOrder(
        user_id=user.id,
        order_no="REFUND-001",
        order_type="recharge",
        amount=Decimal("100.0"),
        actual_amount=Decimal("100.0"),
        status=PaymentStatus.PAID,
        title="Test recharge order",
    )
    db.add(order)
    await db.commit()

    # Create balance account with sufficient balance
    balance_account = UserBalance(
        user_id=user.id,
        balance=Decimal("100.0"),
        total_recharged=Decimal("100.0"),
    )
    db.add(balance_account)
    await db.commit()

    response = await client.post(
        "/api/payment/admin/refund/REFUND-001",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "退款成功"

    # Verify order status updated
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == "REFUND-001")
    )
    updated_order = result.scalar_one_or_none()
    assert updated_order.status == PaymentStatus.REFUNDED


@pytest.mark.asyncio
async def test_admin_refund_already_refunded(client: AsyncClient, db: AsyncSession):
    """Test refund of already refunded order"""
    admin = await UserFactory.create_user(db, username="admin_refund2_test", role="admin")
    user = await UserFactory.create_user(db, username="user_refund2_test")

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    # Create already refunded order
    order = PaymentOrder(
        user_id=user.id,
        order_no="REFUND-002",
        order_type="recharge",
        amount=Decimal("100.0"),
        actual_amount=Decimal("100.0"),
        status=PaymentStatus.REFUNDED,
        title="Test order",
    )
    db.add(order)
    await db.commit()

    response = await client.post(
        "/api/payment/admin/refund/REFUND-002",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "退款成功"


@pytest.mark.asyncio
async def test_admin_refund_pending_order_fails(client: AsyncClient, db: AsyncSession):
    """Test refund of pending order fails"""
    admin = await UserFactory.create_user(db, username="admin_refund3_test", role="admin")
    user = await UserFactory.create_user(db, username="user_refund3_test")

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    # Create pending order
    order = PaymentOrder(
        user_id=user.id,
        order_no="REFUND-003",
        order_type="recharge",
        amount=Decimal("100.0"),
        actual_amount=Decimal("100.0"),
        status=PaymentStatus.PENDING,
        title="Test order",
    )
    db.add(order)
    await db.commit()

    response = await client.post(
        "/api/payment/admin/refund/REFUND-003",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False
    assert "error" in data
    assert "只能退款已支付订单" in str(data["error"])


@pytest.mark.asyncio
async def test_admin_refund_nonexistent_order(client: AsyncClient, db: AsyncSession):
    """Test refund of nonexistent order"""
    admin = await _create_user(db, username="admin_refund4_test", email="admin_refund4@test.com", role="admin")
    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    response = await client.post(
        "/api/payment/admin/refund/NONEXISTENT",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404
    data = response.json()
    assert data["ok"] is False
    assert "error" in data
    assert "订单不存在" in str(data["error"])


@pytest.mark.asyncio
async def test_admin_mark_paid_success(client: AsyncClient, db: AsyncSession):
    """Test marking a pending recharge order as paid"""
    admin = await _create_user(db, username="admin_mark_paid_test", email="admin_mark_paid@test.com", role="admin")
    user = await _create_user(db, username="user_mark_paid_test", email="user_mark_paid@test.com")

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    # Create pending recharge order
    order = await _create_order(
        db,
        user_id=user.id,
        order_no="MARKPAID-001",
        order_type="recharge",
        amount=200.0,
        status=PaymentStatus.PENDING,
    )

    response = await client.post(
        "/api/payment/admin/orders/MARKPAID-001/mark-paid",
        json={"payment_method": "alipay"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "标记成功"

    # Verify order status and balance updated
    result = await db.execute(
        select(PaymentOrder).where(PaymentOrder.order_no == "MARKPAID-001")
    )
    updated_order = result.scalar_one_or_none()
    assert updated_order.status == PaymentStatus.PAID
    assert updated_order.payment_method == "alipay"
    assert updated_order.paid_at is not None

    # Check balance increased
    balance_result = await db.execute(
        select(UserBalance).where(UserBalance.user_id == user.id)
    )
    balance = balance_result.scalar_one_or_none()
    assert balance is not None
    assert float(balance.balance) == 200.0


@pytest.mark.asyncio
async def test_admin_mark_paid_invalid_method(client: AsyncClient, db: AsyncSession):
    """Test marking order paid with invalid payment method"""
    admin = await _create_user(db, username="admin_mark_paid2_test", email="admin_mark_paid2@test.com", role="admin")
    user = await _create_user(db, username="user_mark_paid2_test", email="user_mark_paid2@test.com")

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    await _create_order(
        db,
        user_id=user.id,
        order_no="MARKPAID-002",
        order_type="recharge",
        status=PaymentStatus.PENDING,
    )

    response = await client.post(
        "/api/payment/admin/orders/MARKPAID-002/mark-paid",
        json={"payment_method": "invalid_method"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False
    assert "error" in data
    assert "无效的支付方式" in str(data["error"])


@pytest.mark.asyncio
async def test_admin_mark_paid_non_recharge_order_fails(client: AsyncClient, db: AsyncSession):
    """Test marking non-recharge order as paid fails"""
    admin = await _create_user(db, username="admin_mark_paid3_test", email="admin_mark_paid3@test.com", role="admin")
    user = await _create_user(db, username="user_mark_paid3_test", email="user_mark_paid3@test.com")

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    # Create non-recharge order (e.g., service purchase)
    await _create_order(
        db,
        user_id=user.id,
        order_no="MARKPAID-003",
        order_type="service",
        status=PaymentStatus.PENDING,
    )

    response = await client.post(
        "/api/payment/admin/orders/MARKPAID-003/mark-paid",
        json={"payment_method": "alipay"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False
    assert "error" in data
    assert "仅充值订单支持该操作" in str(data["error"])


@pytest.mark.asyncio
async def test_admin_mark_paid_already_paid(client: AsyncClient, db: AsyncSession):
    """Test marking already paid order as paid returns success"""
    admin = await _create_user(db, username="admin_mark_paid4_test", email="admin_mark_paid4@test.com", role="admin")
    user = await _create_user(db, username="user_mark_paid4_test", email="user_mark_paid4@test.com")

    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    await _create_order(
        db,
        user_id=user.id,
        order_no="MARKPAID-004",
        order_type="recharge",
        status=PaymentStatus.PAID,
    )

    response = await client.post(
        "/api/payment/admin/orders/MARKPAID-004/mark-paid",
        json={"payment_method": "alipay"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert "订单已是支付成功状态" in response.json()["message"]


@pytest.mark.asyncio
async def test_admin_callback_events_list(client: AsyncClient, db: AsyncSession):
    """Test listing payment callback events"""
    admin = await _create_user(db, username="admin_callback_test", email="admin_callback@test.com", role="admin")
    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    # Create callback events
    await _create_callback_event(db, order_no="CB-001", provider="wechat", verified=True)
    await _create_callback_event(db, order_no="CB-002", provider="alipay", verified=False, error_message="Signature mismatch")
    await _create_callback_event(db, order_no="CB-003", provider="wechat", verified=True)

    response = await client.get(
        "/api/payment/admin/callback-events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_admin_callback_events_filters(client: AsyncClient, db: AsyncSession):
    """Test filtering callback events by provider and verified status"""
    admin = await _create_user(db, username="admin_callback2_test", email="admin_callback2@test.com", role="admin")
    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    await _create_callback_event(db, order_no="CB-F1", provider="wechat", verified=True)
    await _create_callback_event(db, order_no="CB-F2", provider="alipay", verified=True)
    await _create_callback_event(db, order_no="CB-F3", provider="wechat", verified=False, error_message="Error")

    # Filter by provider
    response = await client.get(
        "/api/payment/admin/callback-events?provider=wechat",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["provider"] == "wechat"

    # Filter by verified status
    response = await client.get(
        "/api/payment/admin/callback-events?verified=false",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["verified"] is False

    # Filter by has_error
    response = await client.get(
        "/api/payment/admin/callback-events?has_error=true",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_admin_callback_events_pagination(client: AsyncClient, db: AsyncSession):
    """Test pagination of callback events"""
    admin = await _create_user(db, username="admin_callback3_test", email="admin_callback3@test.com", role="admin")
    admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    # Create 5 callback events
    for i in range(1, 6):
        await _create_callback_event(db, order_no=f"CB-P{i}")

    # Test first page
    response = await client.get(
        "/api/payment/admin/callback-events?page=1&page_size=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    # Test second page
    response = await client.get(
        "/api/payment/admin/callback-events?page=2&page_size=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2

    # Test third page (partial)
    response = await client.get(
        "/api/payment/admin/callback-events?page=3&page_size=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


# ============================================================================
# 辅助函数
# ============================================================================

async def _create_user(db: AsyncSession, username: str, email: str = None, role: str = "user") -> User:
    """创建测试用户"""
    from tests.helpers.test_data_factory import UserFactory
    return await UserFactory.create_user(db, username=username, email=email, role=role)


async def _create_order(
    db: AsyncSession,
    user_id: int,
    order_no: str,
    order_type: str = "recharge",
    amount: float = 100.0,
    status = PaymentStatus.PENDING,
) -> PaymentOrder:
    """创建测试订单"""
    order = PaymentOrder(
        user_id=user_id,
        order_no=order_no,
        order_type=order_type,
        amount=amount,
        actual_amount=amount,
        status=status,
        title=f"Test {order_type} order",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def _create_callback_event(
    db: AsyncSession,
    order_no: str,
    provider: str = "wechat",
    verified: bool = True,
    error_message: str = None,
) -> PaymentCallbackEvent:
    """创建测试回调事件"""
    import json
    event = PaymentCallbackEvent(
        order_no=order_no,
        provider=provider,
        raw_payload=json.dumps({"test": "data"}),
        raw_payload_hash="test_hash",
        verified=verified,
        error_message=error_message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
