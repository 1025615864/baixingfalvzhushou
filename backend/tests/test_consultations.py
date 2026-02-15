"""测试AI咨询管理功能"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.consultation import Consultation, ChatMessage
from tests.helpers.test_data_factory import UserFactory, ConsultationFactory


class TestConsultationRoutes:
    """测试咨询管理路由"""
    
    def _get_auth_headers(self, user: User) -> dict[str, str]:
        """获取认证headers"""
        from app.utils.security import create_access_token
        
        token = create_access_token(data={"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_list_consultations_empty(self, client: AsyncClient, test_user: User):
        """测试获取空咨询列表"""
        headers = self._get_auth_headers(test_user)

        response = await client.get("/api/ai/consultations", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_consultations_with_pagination(self, client: AsyncClient, test_user: User):
        """测试分页获取咨询列表"""
        headers = self._get_auth_headers(test_user)

        # 测试不同的分页参数
        response = await client.get("/api/ai/consultations?skip=0&limit=10", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_consultations_with_search(self, client: AsyncClient, test_user: User):
        """测试搜索咨询列表"""
        headers = self._get_auth_headers(test_user)

        # 测试搜索功能
        response = await client.get("/api/ai/consultations?q=test", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_consultation_not_found(self, client: AsyncClient, test_user: User):
        """测试获取不存在的咨询"""
        headers = self._get_auth_headers(test_user)

        response = await client.get("/api/ai/consultations/nonexistent", headers=headers)

        assert response.status_code == 404
        data = response.json()
        assert "ok" in data
        assert data["ok"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_create_share_link_not_found(self, client: AsyncClient, test_user: User):
        """测试为不存在的咨询创建分享链接"""
        headers = self._get_auth_headers(test_user)

        response = await client.post("/api/ai/consultations/nonexistent/share", headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "ok" in data
        assert data["ok"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_delete_consultation_not_found(self, client: AsyncClient, test_user: User):
        """测试删除不存在的咨询"""
        headers = self._get_auth_headers(test_user)

        response = await client.delete("/api/ai/consultations/nonexistent", headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "ok" in data
        assert data["ok"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_export_consultation_not_found(self, client: AsyncClient, test_user: User):
        """测试导出不存在的咨询"""
        headers = self._get_auth_headers(test_user)

        response = await client.get("/api/ai/consultations/nonexistent/export", headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "ok" in data
        assert data["ok"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_list_consultations_unauthorized(self, client: AsyncClient):
        """测试未授权访问咨询列表"""
        response = await client.get("/api/ai/consultations")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_consultation_unauthorized(self, client: AsyncClient):
        """测试未授权获取咨询详情"""
        response = await client.get("/api/ai/consultations/test_session")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_create_share_link_unauthorized(self, client: AsyncClient):
        """测试未授权创建分享链接"""
        response = await client.post("/api/ai/consultations/test/share")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_delete_consultation_unauthorized(self, client: AsyncClient):
        """测试未授权删除咨询"""
        response = await client.delete("/api/ai/consultations/test")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_export_consultation_unauthorized(self, client: AsyncClient):
        """测试未授权导出咨询"""
        response = await client.get("/api/ai/consultations/test/export")
        
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_list_consultations_invalid_limit(self, client: AsyncClient, test_user: User):
        """测试无效的limit参数"""
        headers = self._get_auth_headers(test_user)

        # 测试超过最大限制
        response = await client.get("/api/ai/consultations?limit=200", headers=headers)
        
        # 应该返回422或400
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_list_consultations_invalid_skip(self, client: AsyncClient, test_user: User):
        """测试无效的skip参数"""
        headers = self._get_auth_headers(test_user)

        # 测试负数skip
        response = await client.get("/api/ai/consultations?skip=-1", headers=headers)
        
        # 应该返回422或400
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_share_link_invalid_expires(self, client: AsyncClient, test_user: User):
        """测试无效的expires_days参数"""
        headers = self._get_auth_headers(test_user)

        # 测试超过最大限制
        response = await client.post("/api/ai/consultations/test/share?expires_days=100", headers=headers)
        
        # 应该返回422或400
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_share_link_min_expires(self, client: AsyncClient, test_user: User):
        """测试最小expires_days参数"""
        headers = self._get_auth_headers(test_user)

        # 测试小于最小值
        response = await client.post("/api/ai/consultations/test/share?expires_days=0", headers=headers)
        
        # 应该返回422或400
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_list_consultations_long_query(self, client: AsyncClient, test_user: User):
        """测试过长的查询字符串"""
        headers = self._get_auth_headers(test_user)

        # 测试超过最大长度的查询
        long_query = "a" * 300
        response = await client.get(f"/api/ai/consultations?q={long_query}", headers=headers)
        
        # 应该返回422或400
        assert response.status_code in [400, 422]
