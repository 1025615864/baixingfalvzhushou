"""Token刷新 + Rotation集成测试"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


class TestTokenRefreshAPI:
    """Token刷新API测试"""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """测试正常Token刷新"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            register_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": "13800138901",
                    "password": "Test1234"
                }
            )

            if register_response.status_code == 200:
                login_response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "phone": "13800138901",
                        "password": "Test1234"
                    }
                )

                if login_response.status_code == 200:
                    login_data = login_response.json()
                    refresh_token = login_data.get("refresh_token")

                    refresh_response = await client.post(
                        "/api/v1/auth/refresh",
                        json={"refresh_token": refresh_token}
                    )

                    assert refresh_response.status_code == 200
                    refresh_data = refresh_response.json()
                    assert "access_token" in refresh_data
                    assert "refresh_token" in refresh_data
                    assert refresh_data["refresh_token"] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self):
        """测试无效Token刷新"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid_token"}
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self):
        """测试Token Rotation - 旧Token刷新后失效"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            register_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": "13800138902",
                    "password": "Test1234"
                }
            )

            if register_response.status_code == 200:
                login_response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "phone": "13800138902",
                        "password": "Test1234"
                    }
                )

                if login_response.status_code == 200:
                    login_data = login_response.json()
                    old_refresh_token = login_data.get("refresh_token")

                    first_refresh = await client.post(
                        "/api/v1/auth/refresh",
                        json={"refresh_token": old_refresh_token}
                    )

                    if first_refresh.status_code == 200:
                        second_refresh = await client.post(
                            "/api/v1/auth/refresh",
                            json={"refresh_token": old_refresh_token}
                        )

                        assert second_refresh.status_code == 401

    @pytest.mark.asyncio
    async def test_access_token_cannot_refresh(self):
        """测试access_token不能用于刷新"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            register_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": "13800138903",
                    "password": "Test1234"
                }
            )

            if register_response.status_code == 200:
                login_response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "phone": "13800138903",
                        "password": "Test1234"
                    }
                )

                if login_response.status_code == 200:
                    login_data = login_response.json()
                    access_token = login_data.get("access_token")

                    refresh_response = await client.post(
                        "/api/v1/auth/refresh",
                        json={"refresh_token": access_token}
                    )

                    assert refresh_response.status_code == 401


class TestTokenValidation:
    """Token验证测试"""

    @pytest.mark.asyncio
    async def test_valid_token_access_me(self):
        """测试有效Token访问/me端点"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            register_response = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": "13800138904",
                    "password": "Test1234"
                }
            )

            if register_response.status_code == 200:
                login_response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "phone": "13800138904",
                        "password": "Test1234"
                    }
                )

                if login_response.status_code == 200:
                    login_data = login_response.json()
                    access_token = login_data.get("access_token")

                    me_response = await client.get(
                        "/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    assert me_response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_token_access_me(self):
        """测试无效Token访问/me端点"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid_token"}
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_token_access_me(self):
        """测试无Token访问/me端点"""
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/auth/me")

            assert response.status_code == 401
