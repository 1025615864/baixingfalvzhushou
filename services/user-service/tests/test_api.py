"""API集成测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


class TestAuthAPI:
    """认证API测试"""

    @pytest.mark.asyncio
    async def test_register_endpoint(self):
        """测试注册接口"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": "13800138888",
                    "password": "Test1234"
                }
            )

            assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_login_endpoint(self):
        """测试登录接口"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "phone": "13800138888",
                    "password": "Test1234"
                }
            )

            assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_login_weak_password(self):
        """测试弱密码注册"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": "13800138889",
                    "password": "123"
                }
            )

            assert response.status_code == 400


class TestHealthEndpoints:
    """健康检查端点测试"""

    @pytest.mark.asyncio
    async def test_liveness(self):
        """测试存活检查"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/live")

            assert response.status_code == 200
            assert response.json()["status"] == "alive"

    @pytest.mark.asyncio
    async def test_health(self):
        """测试健康检查"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")

            assert response.status_code == 200
            assert "status" in response.json()


class TestUserEndpoints:
    """用户端点测试"""

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self):
        """测试未授权访问"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/auth/me")

            assert response.status_code == 401


class TestMembershipEndpoints:
    """会员端点测试"""

    @pytest.mark.asyncio
    async def test_get_membership_unauthorized(self):
        """测试未授权访问会员信息"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/membership/info")

            assert response.status_code == 401
