"""法律文书测试"""
import pytest
from httpx import AsyncClient


class TestDocumentEndpoints:
    """文书端点测试"""

    @pytest.mark.asyncio
    async def test_list_templates(self, client: AsyncClient):
        """测试获取文书模板列表"""
        response = await client.get("/api/v1/legal/documents/templates/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_templates_by_category(self, client: AsyncClient):
        """测试按分类获取文书模板"""
        response = await client.get("/api/v1/legal/documents/templates/?category=合同")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_document_requires_auth(self, client: AsyncClient):
        """测试获取文书需要认证"""
        response = await client.get("/api/v1/legal/documents/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_document_requires_auth(self, client: AsyncClient):
        """测试创建文书需要认证"""
        response = await client.post(
            "/api/v1/legal/documents/",
            json={
                "consultation_id": 1,
                "document_type": "合同",
                "title": "测试文书",
            }
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_document_requires_auth(self, client: AsyncClient):
        """测试更新文书需要认证"""
        response = await client.patch(
            "/api/v1/legal/documents/1",
            json={"content": "新内容"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_document_requires_auth(self, client: AsyncClient):
        """测试删除文书需要认证"""
        response = await client.delete("/api/v1/legal/documents/1")
        assert response.status_code == 401


class TestDocumentAuthentication:
    """文书认证测试"""

    @pytest.mark.asyncio
    async def test_get_consultation_documents_requires_auth(self, client: AsyncClient):
        """测试获取咨询文书需要认证"""
        response = await client.get("/api/v1/legal/documents/consultation/1")
        assert response.status_code == 401


class TestDocumentValidation:
    """文书验证测试"""

    @pytest.mark.asyncio
    async def test_create_document_invalid_consultation(self, client: AsyncClient):
        """测试无效咨询ID创建文书"""
        headers = {"Authorization": "Bearer test-token"}
        response = await client.post(
            "/api/v1/legal/documents/",
            headers=headers,
            json={
                "consultation_id": -1,
                "document_type": "合同",
                "title": "测试文书",
            }
        )
        assert response.status_code in [401, 422, 404]

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, client: AsyncClient):
        """测试获取不存在的文书"""
        headers = {"Authorization": "Bearer test-token"}
        response = await client.get(
            "/api/v1/legal/documents/999999",
            headers=headers
        )
        assert response.status_code in [401, 404]
