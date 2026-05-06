"""律所服务测试"""
import pytest
from httpx import AsyncClient


class TestFirmEndpoints:
    """律所端点测试"""

    @pytest.mark.asyncio
    async def test_list_firms(self, client: AsyncClient):
        """测试获取律所列表"""
        response = await client.get("/api/v1/legal/firms/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_list_firms_with_pagination(self, client: AsyncClient):
        """测试律所列表分页"""
        response = await client.get("/api/v1/legal/firms/?skip=0&limit=10")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_firms_filter_by_city(self, client: AsyncClient):
        """测试按城市筛选律所"""
        response = await client.get("/api/v1/legal/firms/?city=北京")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_firm_detail(self, client: AsyncClient):
        """测试获取律所详情"""
        response = await client.get("/api/v1/legal/firms/1")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_firm_lawyers(self, client: AsyncClient):
        """测试获取律所律师"""
        response = await client.get("/api/v1/legal/firms/1/lawyers")
        assert response.status_code in [200, 404]


class TestFirmAuthentication:
    """律所认证测试"""

    @pytest.mark.asyncio
    async def test_create_firm_requires_admin(self, client: AsyncClient):
        """测试创建律所需要管理员权限"""
        response = await client.post(
            "/api/v1/legal/firms/",
            json={
                "name": "测试律所",
                "license_no": "123456",
            }
        )
        assert response.status_code == 401


class TestFirmValidation:
    """律所验证测试"""

    @pytest.mark.asyncio
    async def test_create_firm_invalid_data(self, client: AsyncClient):
        """测试无效数据创建律所"""
        headers = {"Authorization": "Bearer test-admin-token"}
        response = await client.post(
            "/api/v1/legal/firms/",
            headers=headers,
            json={"name": "测试"}
        )
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_firm_not_found(self, client: AsyncClient):
        """测试律所不存在"""
        response = await client.get("/api/v1/legal/firms/999999")
        assert response.status_code == 404
