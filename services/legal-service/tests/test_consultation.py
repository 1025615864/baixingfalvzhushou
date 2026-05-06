"""咨询路由测试"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "legal-service"


@pytest.mark.asyncio
async def test_list_consultations_requires_auth(client: AsyncClient):
    """测试获取咨询列表需要认证"""
    response = await client.get("/api/v1/legal/consultations/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_lawyers_public(client: AsyncClient):
    """测试获取律师列表是公开接口"""
    response = await client.get("/api/v1/legal/lawyers/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_list_firms_public(client: AsyncClient):
    """测试获取律所列表是公开接口"""
    response = await client.get("/api/v1/legal/firms/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_create_consultation_requires_auth(client: AsyncClient):
    """测试创建咨询需要认证"""
    response = await client.post(
        "/api/v1/legal/consultations/",
        json={
            "category": "婚姻继承",
            "title": "离婚财产分割",
            "description": "婚后财产如何分割",
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_metrics(client: AsyncClient):
    """测试指标端点"""
    response = await client.get("/api/v1/legal/metrics")
    assert response.status_code == 200