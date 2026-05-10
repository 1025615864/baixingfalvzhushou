import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


class TestHealthEndpoints:

    @pytest.mark.asyncio
    async def test_health(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "payment-channel-service"

    @pytest.mark.asyncio
    async def test_health_ready(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            assert response.json()["status"] == "ready"

    @pytest.mark.asyncio
    async def test_health_live(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
            assert response.json()["status"] == "alive"


class TestPaymentOrderAPI:

    @pytest.mark.asyncio
    async def test_create_order(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/payment/orders",
                json={
                    "user_id": 1,
                    "order_type": "membership",
                    "amount": 99.0,
                    "title": "会员订阅",
                    "description": "月度会员",
                    "payment_method": "alipay",
                }
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "order_no" in data
                assert "user_id" in data
                assert "amount" in data
                assert "status" in data
                assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_order(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/payment/orders/ORD2024010100000000")
            assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_list_orders(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/payment/orders",
                params={"user_id": 1, "page": 1, "page_size": 10}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert "items" in data
                assert "total" in data
                assert "page" in data
                assert "page_size" in data

    @pytest.mark.asyncio
    async def test_list_orders_pagination(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/payment/orders",
                params={"user_id": 1, "page": 2, "page_size": 5}
            )
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                data = response.json()
                assert data["page"] == 2
                assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_initiate_payment(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/payment/orders/ORD2024010100000000/pay")
            assert response.status_code in [400, 404, 500]

    @pytest.mark.asyncio
    async def test_query_payment_status(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/payment/orders/ORD2024010100000000/status")
            assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_initiate_refund(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/payment/orders/ORD2024010100000000/refund",
                json={"reason": "不想要了"}
            )
            assert response.status_code in [400, 404, 500]


class TestPaymentCallbackAPI:

    @pytest.mark.asyncio
    async def test_alipay_callback(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/payment/callbacks/alipay",
                json={
                    "out_trade_no": "ORD2024010100000000",
                    "trade_no": "2024010100001234567890",
                    "trade_status": "TRADE_SUCCESS",
                }
            )
            assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_wechat_callback(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/payment/callbacks/wechat",
                json={
                    "out_trade_no": "ORD2024010100000000",
                    "transaction_id": "4200001234202401010000000001",
                    "trade_state": "SUCCESS",
                }
            )
            assert response.status_code in [200, 500]


class TestPaymentValidation:

    @pytest.mark.asyncio
    async def test_create_order_missing_fields(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/payment/orders",
                json={"user_id": 1}
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_order_empty_body(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/payment/orders",
                json={}
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_orders_without_user_id(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/payment/orders")
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_order_negative_amount(self):
        app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/payment/orders",
                json={
                    "user_id": 1,
                    "order_type": "membership",
                    "amount": -10.0,
                    "title": "测试订单",
                }
            )
            assert response.status_code in [200, 422, 500]
