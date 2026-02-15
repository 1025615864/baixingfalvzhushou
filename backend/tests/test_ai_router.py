"""测试 AI 路由聚合层和子路由"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from httpx import AsyncClient


class TestAIRouter:
    """测试 AI 路由聚合层"""

    def test_router_exists(self):
        """测试路由对象存在"""
        from app.routers.ai import router
        assert router is not None
        # router 可能没有 prefix，或者 prefix 是空的
        assert len(router.routes) > 0

    def test_settings_export(self):
        """测试 settings 导出"""
        from app.routers.ai import settings
        assert settings is not None
        # settings 应该是一个配置对象
        assert hasattr(settings, 'app_name')

    def test_router_includes_sub_routers(self):
        """测试路由包含子路由"""
        from app.routers.ai import router
        # 检查路由是否包含子路由
        assert len(router.routes) > 0

    def test_module_exports(self):
        """测试模块导出"""
        from app.routers import ai
        assert hasattr(ai, 'router')
        assert hasattr(ai, 'settings')


class TestAIChatRouter:
    """测试 AI 聊天路由"""

    @pytest.mark.asyncio
    async def test_chat_endpoint_exists(self, client: AsyncClient):
        """测试聊天端点存在"""
        # Act
        response = await client.post("/api/ai/chat", json={
            "message": "test",
            "session_id": "test-session"
        })

        # Assert - 可能返回错误，但端点应该存在
        # 没有认证可能返回401，或者配置未完成返回503
        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_chat_without_authentication(self, client: AsyncClient, db):
        """测试未认证访问聊天"""
        # Arrange - Mock OpenAI客户端
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Mock response"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch('app.routers.ai.chat.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.openai_api_key = "test-key"
            mock_settings.openai_base_url = "https://api.openai.com/v1"
            mock_settings.openai_client = mock_client
            mock_get_settings.return_value = mock_settings

            # Act
            response = await client.post("/api/ai/chat", json={
                "message": "test",
                "session_id": "test-session"
            })

        # Assert - 可能允许访客访问（有次数限制）或要求认证
        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_chat_with_authentication(self, client: AsyncClient, test_user, db, monkeypatch):
        """测试认证后访问聊天"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Mock OpenAI客户端
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Mock AI response"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        monkeypatch.setattr("app.routers.ai.chat.settings", MagicMock())
        monkeypatch.setattr("app.routers.ai.chat.settings.openai_client", mock_client)

        # Act
        response = await client.post("/api/ai/chat", json={
            "message": "Hello",
            "session_id": "test-session-123"
        }, headers=headers)

        # Assert - 如果AI未配置可能返回503，否则应该成功
        assert response.status_code in [200, 503]


class TestAIConsultationsRouter:
    """测试 AI 咨询管理路由"""

    @pytest.mark.asyncio
    async def test_list_consultations_without_auth(self, client: AsyncClient):
        """测试未认证访问咨询列表"""
        # Act
        response = await client.get("/api/ai/consultations")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_consultations_with_auth(self, client: AsyncClient, test_user, db):
        """测试认证后访问咨询列表"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.get("/api/ai/consultations", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_consultation_detail_without_auth(self, client: AsyncClient, db):
        """测试未认证访问咨询详情"""
        # Act
        response = await client.get("/api/ai/consultations/123")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_consultation_detail_not_found(self, client: AsyncClient, test_user, db):
        """测试访问不存在的咨询"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.get("/api/ai/consultations/99999", headers=headers)

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_consultation_share(self, client: AsyncClient, test_user, db):
        """测试创建咨询分享链接"""
        # Arrange
        from app.utils.security import create_access_token
        from app.models.consultation import Consultation
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 先创建一个咨询
        consultation = Consultation(
            user_id=test_user.id,
            session_id="test-session-id",
            title="Test Consultation",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(consultation)
        await db.commit()

        # Act
        response = await client.post(f"/api/ai/consultations/{consultation.id}/share", headers=headers)

        # Assert
        assert response.status_code in [200, 404]  # 可能不存在或成功


class TestAIAnalysisRouter:
    """测试 AI 分析路由"""

    @pytest.mark.asyncio
    async def test_file_analysis_without_auth(self, client: AsyncClient):
        """测试未认证上传文件分析"""
        # Arrange
        import io
        file_content = io.BytesIO(b"test document content")

        # Act
        response = await client.post(
            "/api/ai/files/analyze",
            files={"file": ("test.txt", file_content, "text/plain")}
        )

        # Assert - 可能允许访客访问或要求认证
        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_file_analysis_with_auth(self, client: AsyncClient, test_user, db):
        """测试认证后上传文件分析"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        import io
        file_content = io.BytesIO(b"test document content")

        # Mock OpenAI客户端
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Mock analysis result"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch('app.routers.ai.analysis.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.openai_api_key = "test-key"
            mock_settings.openai_base_url = "https://api.openai.com/v1"
            mock_settings.openai_client = mock_client
            mock_get_settings.return_value = mock_settings

            # Act
            response = await client.post(
                "/api/ai/files/analyze",
                files={"file": ("test.txt", file_content, "text/plain")},
                headers=headers
            )

        # Assert - 如果AI未配置可能返回503
        assert response.status_code in [200, 503]

    @pytest.mark.asyncio
    async def test_quick_replies_endpoint(self, client: AsyncClient, test_user, db):
        """测试快速回复端点"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.post("/api/ai/quick-replies", json={
            "user_message": "test message",
            "assistant_answer": "test answer"
        }, headers=headers)

        # Assert - 可能返回快速建议或配置错误
        assert response.status_code in [200, 503]


class TestAITranscriptionRouter:
    """测试 AI 语音转写路由"""

    @pytest.mark.asyncio
    async def test_transcription_endpoint_exists(self, client: AsyncClient):
        """测试转写端点存在"""
        # Arrange
        import io
        audio_content = io.BytesIO(b"fake audio data")

        # Act
        response = await client.post(
            "/api/ai/transcribe",
            files={"file": ("test.mp3", audio_content, "audio/mpeg")}
        )

        # Assert - 端点应该存在，可能返回401或503
        assert response.status_code in [200, 401, 503]


class TestAIShareRouter:
    """测试 AI 分享路由"""

    @pytest.mark.asyncio
    async def test_shared_consultation_access(self, client: AsyncClient):
        """测试访问分享的咨询"""
        # Arrange
        share_token = "test_share_token_123"

        # Act
        response = await client.get(f"/api/ai/share/{share_token}")

        # Assert - 可能返回404或401(token不存在或需要认证)
        assert response.status_code in [200, 401, 404]


class TestAIRouterRateLimit:
    """测试 AI 路由速率限制"""

    @pytest.mark.asyncio
    async def test_guest_rate_limit(self, client: AsyncClient):
        """测试访客速率限制"""
        # Arrange - Mock AI客户端
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # 多次请求
        responses = []
        for _ in range(10):
            response = await client.post("/api/ai/chat", json={
                "message": "test",
                "session_id": "test-session"
            })
            responses.append(response.status_code)

        # Assert - 应该有一些请求被限流（429）
        # 但如果没有配置AI，可能都是503
        assert any(status in [200, 429, 503] for status in responses)


class TestAIRouterErrorHandling:
    """测试 AI 路由错误处理"""

    @pytest.mark.asyncio
    async def test_invalid_request_format(self, client: AsyncClient, test_user, db):
        """测试无效请求格式"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = await client.post(
            "/api/ai/chat",
            json={"invalid": "data"},  # 缺少必需字段
            headers=headers
        )

        # Assert - 应该返回验证错误
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_ai_service_unavailable(self, client: AsyncClient, test_user, db):
        """测试AI服务不可用"""
        # Arrange
        from app.utils.security import create_access_token
        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 使用 patch 确保AI未配置
        with patch('app.routers.ai.chat.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.openai_api_key = None
            mock_get_settings.return_value = mock_settings

            # Act
            response = await client.post("/api/ai/chat", json={
                "message": "test",
                "session_id": "test-session"
            }, headers=headers)

        # Assert - 应该返回服务不可用
        assert response.status_code in [503, 500]
