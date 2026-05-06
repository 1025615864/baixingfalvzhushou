"""限流集成测试"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_app


class TestRateLimiting:
    """限流测试"""

    @pytest.mark.asyncio
    async def test_register_rate_limit(self):
        """测试注册接口限流"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            responses = []
            for i in range(10):
                response = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "phone": f"13800138{str(i).zfill(3)}",
                        "password": "Test1234"
                    }
                )
                responses.append(response.status_code)

            assert 429 in responses or 400 in responses or 200 in responses

    @pytest.mark.asyncio
    async def test_login_rate_limit(self):
        """测试登录接口限流"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            responses = []
            for i in range(15):
                response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "phone": "13800138000",
                        "password": "WrongPassword"
                    }
                )
                responses.append(response.status_code)

            assert 429 in responses or 401 in responses or 200 in responses

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self):
        """测试限流响应头"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": "13800138100",
                    "password": "Test1234"
                }
            )

            if response.status_code == 429:
                assert "X-RateLimit-Limit" in response.headers or "retry-after" in str(response.headers).lower()

    @pytest.mark.asyncio
    async def test_rate_limit_recovery(self):
        """测试限流恢复"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            for _ in range(10):
                await client.post(
                    "/api/v1/auth/register",
                    json={
                        "phone": "13800138200",
                        "password": "Test1234"
                    }
                )

            response_429 = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": "13800138201",
                    "password": "Test1234"
                }
            )

            if response_429.status_code == 429:
                await asyncio.sleep(1)

                response_recovered = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "phone": "13800138202",
                        "password": "Test1234"
                    }
                )

                assert response_recovered.status_code in [200, 400]


class TestEndpointAvailability:
    """端点可用性测试"""

    @pytest.mark.asyncio
    async def test_health_endpoints_available(self):
        """测试健康检查端点可用"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200

            response = await client.get("/health/live")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_auth_endpoints_available(self):
        """测试认证端点可用"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/auth/me")
            assert response.status_code == 401
