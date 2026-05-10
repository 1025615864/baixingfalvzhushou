import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


class TestHealthEndpoints:

    @pytest.mark.asyncio
    async def test_health(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "order-service"

    @pytest.mark.asyncio
    async def test_health_ready(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_health_live(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"


class TestOrderAPI:

    @pytest.mark.asyncio
    async def test_create_order(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/orders/",
                params={
                    "order_type": "legal_consultation",
                    "title": "法律咨询订单",
                    "amount": 100.0,
                }
            )
            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert "order_no" in data
            assert data["status"] == "pending"
            assert data["amount"] == 100.0

    @pytest.mark.asyncio
    async def test_create_order_with_discount(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/orders/",
                params={
                    "order_type": "document_service",
                    "title": "文书服务订单",
                    "amount": 200.0,
                    "discount_amount": 50.0,
                }
            )
            assert response.status_code == 201
            data = response.json()
            assert data["actual_amount"] == 150.0

    @pytest.mark.asyncio
    async def test_get_order(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            create_resp = await client.post(
                "/api/v1/orders/",
                params={
                    "order_type": "membership",
                    "title": "会员订单",
                    "amount": 50.0,
                }
            )
            order_id = create_resp.json()["id"]
            response = await client.get(f"/api/v1/orders/{order_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == order_id
            assert "order_no" in data
            assert "status" in data

    @pytest.mark.asyncio
    async def test_get_order_not_found(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/orders/999999")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_orders(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/orders/")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "offset" in data
            assert "limit" in data

    @pytest.mark.asyncio
    async def test_list_orders_pagination(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/orders/",
                params={"offset": 0, "limit": 5}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["offset"] == 0
            assert data["limit"] == 5
            assert len(data["items"]) <= 5

    @pytest.mark.asyncio
    async def test_pay_order(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            create_resp = await client.post(
                "/api/v1/orders/",
                params={
                    "order_type": "legal_consultation",
                    "title": "待支付订单",
                    "amount": 80.0,
                }
            )
            order_no = create_resp.json()["order_no"]
            response = await client.post(
                f"/api/v1/orders/{order_no}/pay",
                params={"payment_method": "alipay"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "paid"
            assert data["payment_method"] == "alipay"

    @pytest.mark.asyncio
    async def test_cancel_order(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            create_resp = await client.post(
                "/api/v1/orders/",
                params={
                    "order_type": "other",
                    "title": "待取消订单",
                    "amount": 30.0,
                }
            )
            order_no = create_resp.json()["order_no"]
            response = await client.post(
                f"/api/v1/orders/{order_no}/cancel",
                params={"reason": "不想要了"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_non_pending_order_returns_error(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            create_resp = await client.post(
                "/api/v1/orders/",
                params={
                    "order_type": "legal_consultation",
                    "title": "已支付订单",
                    "amount": 60.0,
                }
            )
            order_no = create_resp.json()["order_no"]
            await client.post(
                f"/api/v1/orders/{order_no}/pay",
                params={"payment_method": "wechatpay"}
            )
            response = await client.post(
                f"/api/v1/orders/{order_no}/cancel"
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_complete_order(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            create_resp = await client.post(
                "/api/v1/orders/",
                params={
                    "order_type": "document_service",
                    "title": "待完成订单",
                    "amount": 120.0,
                }
            )
            order_no = create_resp.json()["order_no"]
            await client.post(
                f"/api/v1/orders/{order_no}/pay",
                params={"payment_method": "balance"}
            )
            response = await client.post(
                f"/api/v1/orders/{order_no}/complete"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_refund_order(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            create_resp = await client.post(
                "/api/v1/orders/",
                params={
                    "order_type": "membership",
                    "title": "待退款订单",
                    "amount": 99.0,
                }
            )
            order_no = create_resp.json()["order_no"]
            await client.post(
                f"/api/v1/orders/{order_no}/pay",
                params={"payment_method": "alipay"}
            )
            response = await client.post(
                f"/api/v1/orders/{order_no}/refund",
                params={"reason": "服务不满意"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "refunded"

    @pytest.mark.asyncio
    async def test_admin_order_stats(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/orders/admin/stats",
                params={
                    "start_date": "2024-01-01T00:00:00",
                    "end_date": "2026-12-31T23:59:59",
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "total_orders" in data
            assert "total_revenue" in data
            assert "orders_by_status" in data

    @pytest.mark.asyncio
    async def test_admin_order_stats_invalid_dates(self):
        application = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=application),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/orders/admin/stats",
                params={
                    "start_date": "2026-12-31T23:59:59",
                    "end_date": "2024-01-01T00:00:00",
                }
            )
            assert response.status_code == 400
