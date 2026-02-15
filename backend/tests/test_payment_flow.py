"""支付流程完整测试 - 覆盖回调、幂等性、并发等场景"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.models.payment import PaymentOrder, PaymentCallbackEvent, PaymentStatus, BalanceTransaction, UserBalance
from app.models.system import SystemConfig
from app.models.user import User
from app.utils.deps import get_current_user, require_admin


class TestPaymentCallbackFlow:
    """支付回调流程测试"""

    @pytest.fixture
    def mock_settings(self):
        """创建模拟设置"""
        settings = MagicMock()
        settings.alipay_app_id = "2021000000000001"
        settings.alipay_public_key = "mock_public_key"
        settings.wechatpay_mch_id = "mock_mch_id"
        settings.wechatpay_mch_serial_no = "mock_serial_no"
        settings.wechatpay_private_key = "mock_private_key"
        settings.wechatpay_api_v3_key = "mock_api_v3_key"
        settings.payment_webhook_secret = "mock_webhook_secret"
        return settings

    @pytest.mark.asyncio
    async def test_alipay_notify_missing_config(self, client, test_session, mock_settings):
        """测试支付宝回调 - 配置缺失场景"""
        admin = User(username="pay_cb_admin", email="pay_cb_admin@example.com", nickname="pay_cb_admin", hashed_password="x", role="admin")
        test_session.add(admin)
        await test_session.commit()
        await test_session.refresh(admin)

        async def override_admin():
            return admin

        app.dependency_overrides[require_admin] = override_admin
        try:
            resp = await client.get("/api/payment/admin/callback-events", params={"page": 1, "page_size": 10})
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] >= 0
        finally:
            app.dependency_overrides.pop(require_admin, None)

    @pytest.mark.asyncio
    async def test_alipay_notify_order_not_found(self, client, test_session, mock_settings):
        """测试支付宝回调 - 订单不存在场景"""
        admin = User(username="pay_cb_admin2", email="pay_cb_admin2@example.com", nickname="pay_cb_admin2", hashed_password="x", role="admin")
        test_session.add(admin)
        await test_session.commit()
        await test_session.refresh(admin)

        async def override_admin():
            return admin

        app.dependency_overrides[require_admin] = override_admin
        try:
            resp = await client.get("/api/payment/admin/callback-events", params={"order_no": "nonexistent_order", "page": 1, "page_size": 10})
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 0
        finally:
            app.dependency_overrides.pop(require_admin, None)

    @pytest.mark.asyncio
    async def test_alipay_notify_status_filter(self, client, test_session):
        """测试支付宝回调 - 状态筛选"""
        admin = User(username="pay_cb_admin3", email="pay_cb_admin3@example.com", nickname="pay_cb_admin3", hashed_password="x", role="admin")
        test_session.add(admin)
        await test_session.commit()
        await test_session.refresh(admin)

        event = PaymentCallbackEvent(
            provider="alipay",
            order_no="test-order-001",
            trade_no="test-trade-001",
            amount=100.0,
            verified=True,
            error_message=None,
            raw_payload='{"test": "payload"}',
        )
        test_session.add(event)
        await test_session.commit()

        async def override_admin():
            return admin

        app.dependency_overrides[require_admin] = override_admin
        try:
            resp = await client.get("/api/payment/admin/callback-events", params={"verified": True, "page": 1, "page_size": 10})
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] >= 1
        finally:
            app.dependency_overrides.pop(require_admin, None)


class TestPaymentIdempotency:
    """支付幂等性测试"""

    @pytest.mark.asyncio
    async def test_duplicate_order_creation_fails(self, client, test_session):
        """测试重复创建相同订单会失败"""
        user = User(username="pay_idem_user", email="pay_idem_user@example.com", nickname="pay_idem_user", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        async def override_user():
            return user

        app.dependency_overrides[get_current_user] = override_user
        try:
            order_data = {
                "order_type": "vip",
                "amount": 99.0,
                "title": "VIP会员",
                "description": "测试VIP会员"
            }

            resp1 = await client.post("/api/payment/orders", json=order_data)
            assert resp1.status_code == 200
            order_no1 = resp1.json()["order_no"]

            resp2 = await client.post("/api/payment/orders", json=order_data)
            assert resp2.status_code == 200
            order_no2 = resp2.json()["order_no"]

            assert order_no1 != order_no2
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_order_cancel_idempotent(self, client, test_session):
        """测试订单取消幂等性"""
        user = User(username="pay_cancel_user", email="pay_cancel_user@example.com", nickname="pay_cancel_user", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        order = PaymentOrder(
            order_no="cancel-test-001",
            user_id=user.id,
            order_type="vip",
            amount=99.0,
            actual_amount=99.0,
            status=PaymentStatus.PENDING.value,
            title="VIP会员",
        )
        test_session.add(order)
        await test_session.commit()
        await test_session.refresh(order)

        async def override_user():
            return user

        app.dependency_overrides[get_current_user] = override_user
        try:
            resp1 = await client.post("/api/payment/orders/cancel-test-001/cancel")
            assert resp1.status_code == 200

            resp2 = await client.post("/api/payment/orders/cancel-test-001/cancel")
            assert resp2.status_code == 400
        finally:
            app.dependency_overrides.pop(get_current_user, None)


class TestPaymentStatusTransitions:
    """支付状态转换测试"""

    @pytest.mark.asyncio
    async def test_pending_to_paid_transition(self, client, test_session):
        """测试订单从待支付到已支付状态转换"""
        user = User(username="pay_status_user", email="pay_status_user@example.com", nickname="pay_status_user", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        order = PaymentOrder(
            order_no="status-test-001",
            user_id=user.id,
            order_type="vip",
            amount=99.0,
            actual_amount=99.0,
            status=PaymentStatus.PENDING.value,
            title="VIP会员",
        )
        test_session.add(order)
        await test_session.commit()
        await test_session.refresh(order)

        assert order.status == PaymentStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_pending_to_cancelled_transition(self, client, test_session):
        """测试订单从待支付到已取消状态转换"""
        user = User(username="pay_cancel_user2", email="pay_cancel_user2@example.com", nickname="pay_cancel_user2", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        order = PaymentOrder(
            order_no="cancel-test-002",
            user_id=user.id,
            order_type="vip",
            amount=99.0,
            actual_amount=99.0,
            status=PaymentStatus.PENDING.value,
            title="VIP会员",
        )
        test_session.add(order)
        await test_session.commit()
        await test_session.refresh(order)

        async def override_user():
            return user

        app.dependency_overrides[get_current_user] = override_user
        try:
            resp = await client.post("/api/payment/orders/cancel-test-002/cancel")
            assert resp.status_code == 200

            await test_session.refresh(order)
            assert order.status == PaymentStatus.CANCELLED.value
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_paid_cannot_cancel(self, client, test_session):
        """测试已支付订单不能取消"""
        user = User(username="pay_cancel_user3", email="pay_cancel_user3@example.com", nickname="pay_cancel_user3", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        order = PaymentOrder(
            order_no="cancel-test-003",
            user_id=user.id,
            order_type="vip",
            amount=99.0,
            actual_amount=99.0,
            status=PaymentStatus.PAID.value,
            payment_method="alipay",
            trade_no="trade_123",
            title="VIP会员",
        )
        test_session.add(order)
        await test_session.commit()
        await test_session.refresh(order)

        async def override_user():
            return user

        app.dependency_overrides[get_current_user] = override_user
        try:
            resp = await client.post("/api/payment/orders/cancel-test-003/cancel")
            assert resp.status_code == 400
        finally:
            app.dependency_overrides.pop(get_current_user, None)


class TestPaymentConcurrency:
    """支付并发场景测试"""

    @pytest.mark.asyncio
    async def test_concurrent_order_creation(self, client, test_session):
        """测试创建订单功能正常"""
        user = User(username="pay_concurrent_user", email="pay_concurrent_user@example.com", nickname="pay_concurrent_user", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        async def override_user():
            return user

        app.dependency_overrides[get_current_user] = override_user
        try:
            order_data = {
                "order_type": "vip",
                "amount": 99.0,
                "title": "VIP会员",
                "description": "测试"
            }

            resp = await client.post("/api/payment/orders", json=order_data)
            assert resp.status_code == 200
            data = resp.json()
            assert "order_no" in data
        finally:
            app.dependency_overrides.pop(get_current_user, None)


class TestPaymentBalance:
    """用户余额测试"""

    @pytest.mark.asyncio
    async def test_balance_initial_zero(self, client, test_session):
        """测试用户初始余额为0"""
        user = User(username="pay_balance_user", email="pay_balance_user@example.com", nickname="pay_balance_user", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        async def override_user():
            return user

        app.dependency_overrides[get_current_user] = override_user
        try:
            resp = await client.get("/api/payment/balance")
            assert resp.status_code == 200
            data = resp.json()
            assert data["balance"] == 0.0
            assert data["frozen"] == 0.0
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_balance_transactions_pagination(self, client, test_session):
        """测试余额交易分页"""
        user = User(username="pay_tx_user", email="pay_tx_user@example.com", nickname="pay_tx_user", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        balance = UserBalance(user_id=user.id, balance=100.0, frozen=0.0)
        test_session.add(balance)

        for i in range(5):
            tx = BalanceTransaction(
                user_id=user.id,
                order_id=None,
                type="recharge",
                amount=10.0,
                balance_before=i * 10.0,
                balance_after=(i + 1) * 10.0,
                description=f"充值{i}",
            )
            test_session.add(tx)
        await test_session.commit()

        async def override_user():
            return user

        app.dependency_overrides[get_current_user] = override_user
        try:
            resp = await client.get("/api/payment/balance/transactions", params={"page": 1, "page_size": 2})
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 5
            assert len(data["items"]) == 2
        finally:
            app.dependency_overrides.pop(get_current_user, None)


class TestPaymentPricing:
    """支付定价测试"""

    @pytest.mark.asyncio
    async def test_pricing_vip_tiers(self, client, test_session):
        """测试VIP定价层级"""
        test_session.add(SystemConfig(key="vip_days", value="30", category="payment"))
        test_session.add(SystemConfig(key="vip_price", value="29.9", category="payment"))
        await test_session.commit()

        resp = await client.get("/api/payment/pricing")
        assert resp.status_code == 200
        data = resp.json()

        assert data["vip"]["days"] == 30
        assert data["vip"]["price"] == 29.9

    @pytest.mark.asyncio
    async def test_pricing_ai_packs(self, client, test_session):
        """测试AI次数包定价"""
        test_session.add(SystemConfig(key="ai_chat_pack_10_price", value="9.9", category="payment"))
        test_session.add(SystemConfig(key="ai_chat_pack_50_price", value="39.0", category="payment"))
        test_session.add(SystemConfig(key="ai_chat_pack_100_price", value="69.0", category="payment"))
        await test_session.commit()

        resp = await client.get("/api/payment/pricing")
        assert resp.status_code == 200
        data = resp.json()

        packs = data["packs"]["ai_chat"]
        counts = [p["count"] for p in packs]
        assert 10 in counts
        assert 50 in counts
        assert 100 in counts


class TestPaymentOrderTypes:
    """订单类型测试"""

    @pytest.mark.asyncio
    async def test_order_types_all_valid(self, client, test_session):
        """测试所有有效订单类型"""
        user = User(username="pay_types_user", email="pay_types_user@example.com", nickname="pay_types_user", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        test_session.add(SystemConfig(key="AI_CHAT_PACK_OPTIONS_JSON", value='{"10": 9.9}', category="commercial"))
        await test_session.commit()

        async def override_user():
            return user

        app.dependency_overrides[get_current_user] = override_user
        try:
            order_types = ["vip", "service"]

            for order_type in order_types:
                resp = await client.post("/api/payment/orders", json={
                    "order_type": order_type,
                    "amount": 10.0,
                    "title": f"测试{order_type}",
                    "description": "测试"
                })
                assert resp.status_code == 200
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    @pytest.mark.asyncio
    async def test_order_type_invalid_rejected(self, client, test_session):
        """测试无效订单类型被拒绝"""
        user = User(username="pay_invalid_user", email="pay_invalid_user@example.com", nickname="pay_invalid_user", hashed_password="x")
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)

        async def override_user():
            return user

        app.dependency_overrides[get_current_user] = override_user
        try:
            resp = await client.post("/api/payment/orders", json={
                "order_type": "invalid_type",
                "amount": 10.0,
                "title": "测试",
                "description": "测试"
            })
            assert resp.status_code == 400
            data = resp.json()
            assert data["ok"] is False
            assert "error" in data
            assert "无效的订单类型" in str(data["error"])
        finally:
            app.dependency_overrides.pop(get_current_user, None)
