"""律师服务测试"""
import pytest
from httpx import AsyncClient


class TestLawyerEndpoints:
    """律师端点测试"""

    @pytest.mark.asyncio
    async def test_list_lawyers(self, client: AsyncClient):
        """测试获取律师列表"""
        response = await client.get("/api/v1/legal/lawyers/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_lawyers_with_pagination(self, client: AsyncClient):
        """测试律师列表分页"""
        response = await client.get("/api/v1/legal/lawyers/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 10

    @pytest.mark.asyncio
    async def test_list_lawyers_filter_by_city(self, client: AsyncClient):
        """测试按城市筛选律师"""
        response = await client.get("/api/v1/legal/lawyers/?city=北京")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_lawyers_filter_by_specialty(self, client: AsyncClient):
        """测试按专业筛选律师"""
        response = await client.get("/api/v1/legal/lawyers/?specialty=刑事辩护")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_lawyer_detail(self, client: AsyncClient):
        """测试获取律师详情"""
        response = await client.get("/api/v1/legal/lawyers/1")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_lawyer_reviews(self, client: AsyncClient):
        """测试获取律师评价"""
        response = await client.get("/api/v1/legal/lawyers/1/reviews")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_lawyer_schedule(self, client: AsyncClient):
        """测试获取律师日程"""
        response = await client.get("/api/v1/legal/lawyers/1/schedule?date=2024-01-15")
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_search_lawyers(self, client: AsyncClient):
        """测试搜索律师"""
        response = await client.get("/api/v1/legal/lawyers/search?q=离婚")
        assert response.status_code == 200


class TestLawyerAuthentication:
    """律师认证测试"""

    @pytest.mark.asyncio
    async def test_create_lawyer_requires_auth(self, client: AsyncClient):
        """测试创建律师需要认证"""
        response = await client.post(
            "/api/v1/legal/lawyers/",
            json={
                "user_id": 1,
                "name": "测试律师",
                "title": "合伙人",
                "specialties": ["婚姻家庭"],
            }
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_lawyer_requires_auth(self, client: AsyncClient):
        """测试更新律师需要认证"""
        response = await client.patch(
            "/api/v1/legal/lawyers/1",
            json={"title": "高级合伙人"}
        )
        assert response.status_code == 401


class TestLawyerValidation:
    """律师验证测试"""

    @pytest.mark.asyncio
    async def test_create_lawyer_invalid_data(self, client: AsyncClient):
        """测试无效数据创建律师"""
        headers = {"Authorization": "Bearer test-token"}
        response = await client.post(
            "/api/v1/legal/lawyers/",
            headers=headers,
            json={"name": "测试"}
        )
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_lawyer_not_found(self, client: AsyncClient):
        """测试律师不存在"""
        response = await client.get("/api/v1/legal/lawyers/999999")
        assert response.status_code == 404
