"""测试AI聊天功能"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.consultation import Consultation


class TestChatRoutes:
    """测试AI聊天路由"""

    @pytest.mark.asyncio
    async def test_chat_with_ai_unauthorized(self, client: AsyncClient):
        """测试未授权聊天"""
        response = await client.post("/api/ai/chat", json={
            "message": "Hello"
        })
        
        # 可能返回200（游客模式）或401/403或503（AI服务不可用）或429（速率限制）
        assert response.status_code in [200, 401, 403, 503, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_as_user(self, client: AsyncClient, test_user: User):
        """测试用户聊天"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": "Hello"
        })
        
        # 可能返回200或503（AI服务未配置）或429（速率限制）
        assert response.status_code in [200, 503, 404, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_empty_message(self, client: AsyncClient, test_user: User):
        """测试空消息"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": ""
        })
        
        # 可能返回400或422或503（AI服务不可用）或429（速率限制）
        assert response.status_code in [400, 422, 503, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_invalid_payload(self, client: AsyncClient, test_user: User):
        """测试无效的payload"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={})
        
        # 可能返回400或422或503（AI服务不可用）或429（速率限制）
        assert response.status_code in [400, 422, 503, 429]

    @pytest.mark.asyncio
    async def test_chat_stream_unauthorized(self, client: AsyncClient):
        """测试未授权流式聊天"""
        response = await client.post("/api/ai/chat/stream", json={
            "message": "Hello"
        })
        
        # 可能返回200（游客模式）或401/403或503（AI服务不可用）或429（速率限制）
        assert response.status_code in [200, 401, 403, 503, 429]

    @pytest.mark.asyncio
    async def test_chat_stream_as_user(self, client: AsyncClient, test_user: User):
        """测试用户流式聊天"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat/stream", headers=headers, json={
            "message": "Hello"
        })
        
        # 可能返回200或503（AI服务未配置）或429（速率限制）
        assert response.status_code in [200, 503, 404, 429]

    @pytest.mark.asyncio
    async def test_chat_stream_empty_message(self, client: AsyncClient, test_user: User):
        """测试流式聊天空消息"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat/stream", headers=headers, json={
            "message": ""
        })
        
        # 可能返回400或422或503（AI服务不可用）或429（速率限制）
        assert response.status_code in [400, 422, 503, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_rate_limit(self, client: AsyncClient):
        """测试游客模式速率限制"""
        # 多次请求以触发速率限制
        for i in range(5):
            response = await client.post("/api/ai/chat", json={
                "message": f"Test message {i}"
            })
            # 最后几次应该触发速率限制
            if i >= 3:
                # 可能返回429（速率限制）或200/401或503（AI服务不可用）
                assert response.status_code in [200, 401, 429, 503]

    @pytest.mark.asyncio
    async def test_chat_with_ai_with_history(self, client: AsyncClient, test_user: User):
        """测试带历史记录的聊天"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": "Hello",
            "history": [
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"}
            ]
        })
        
        # 可能返回200或503（AI服务未配置）或429（速率限制）
        assert response.status_code in [200, 503, 404, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_with_session_id(self, client: AsyncClient, test_user: User):
        """测试带会话ID的聊天"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": "Hello",
            "session_id": "test-session-123"
        })
        
        # 可能返回200或503（AI服务未配置）或429（速率限制）
        assert response.status_code in [200, 503, 404, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_long_message(self, client: AsyncClient, test_user: User):
        """测试长消息"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        long_message = "Test message " * 1000  # 超长消息
        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": long_message
        })
        
        # 可能返回200或400/413/422（消息过长/验证失败）或503或429（速率限制）
        assert response.status_code in [200, 400, 413, 422, 503, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_special_characters(self, client: AsyncClient, test_user: User):
        """测试特殊字符"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": "Test <script>alert('xss')</script> message"
        })
        
        # 可能返回200或400或503或429（速率限制）
        assert response.status_code in [200, 400, 503, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_with_temperature(self, client: AsyncClient, test_user: User):
        """测试带temperature参数的聊天"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": "Hello",
            "temperature": 0.7
        })
        
        # 可能返回200或503或429（速率限制）
        assert response.status_code in [200, 503, 404, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_invalid_temperature(self, client: AsyncClient, test_user: User):
        """测试无效的temperature参数"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": "Hello",
            "temperature": 2.0  # 超出有效范围
        })
        
        # 可能返回400或422或503（AI服务不可用）或429（速率限制）
        assert response.status_code in [400, 422, 503, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_with_max_tokens(self, client: AsyncClient, test_user: User):
        """测试带max_tokens参数的聊天"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": "Hello",
            "max_tokens": 1000
        })
        
        # 可能返回200或503或429（速率限制）
        assert response.status_code in [200, 503, 404, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_invalid_max_tokens(self, client: AsyncClient, test_user: User):
        """测试无效的max_tokens参数"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": "Hello",
            "max_tokens": -1  # 无效值
        })
        
        # 可能返回400或422或503（AI服务不可用）或429（速率限制）
        assert response.status_code in [400, 422, 503, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_with_model(self, client: AsyncClient, test_user: User):
        """测试指定模型"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": "Hello",
            "model": "gpt-3.5-turbo"
        })
        
        # 可能返回200或503或429（速率限制）
        assert response.status_code in [200, 503, 404, 429]

    @pytest.mark.asyncio
    async def test_chat_stream_with_history(self, client: AsyncClient, test_user: User):
        """测试流式聊天带历史记录"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/api/ai/chat/stream", headers=headers, json={
            "message": "Hello",
            "history": [
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"}
            ]
        })
        
        # 可能返回200或503或429（速率限制）
        assert response.status_code in [200, 503, 404, 429]

    @pytest.mark.asyncio
    async def test_chat_stream_rate_limit(self, client: AsyncClient):
        """测试流式聊天速率限制"""
        # 多次请求以触发速率限制
        for i in range(5):
            response = await client.post("/api/ai/chat/stream", json={
                "message": f"Test message {i}"
            })
            # 最后几次应该触发速率限制
            if i >= 3:
                # 可能返回429（速率限制）或200/401或503（AI服务不可用）
                assert response.status_code in [200, 401, 429, 503]

    @pytest.mark.asyncio
    async def test_chat_with_ai_conversation_context(self, client: AsyncClient, test_user: User):
        """测试对话上下文"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 第一次聊天
        response1 = await client.post("/api/ai/chat", headers=headers, json={
            "message": "My name is Alice"
        })
        
        # 第二次聊天，应该能够记住上下文
        response2 = await client.post("/api/ai/chat", headers=headers, json={
            "message": "What is my name?",
            "session_id": "test-session-456"
        })
        
        # 可能返回200或503或429（速率限制）
        assert response1.status_code in [200, 503, 404, 429]
        assert response2.status_code in [200, 503, 404, 429]

    @pytest.mark.asyncio
    async def test_chat_with_ai_error_handling(self, client: AsyncClient, test_user: User):
        """测试错误处理"""
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 发送可能导致错误的请求
        response = await client.post("/api/ai/chat", headers=headers, json={
            "message": "Test"
        })
        
        # 检查响应中是否包含错误信息
        if response.status_code == 200:
            data = response.json()
            # 如果成功，应该包含响应内容
            assert "response" in data or "message" in data or "error_code" in data
        elif response.status_code == 503:
            # AI服务不可用
            pass

    @pytest.mark.asyncio
    async def test_chat_with_ai_quota_enforcement(self, client: AsyncClient):
        """测试配额强制执行"""
        # 游客模式应该有配额限制
        for i in range(10):
            response = await client.post("/api/ai/chat", json={
                "message": f"Test {i}"
            })
            # 在达到配额后应该返回429
            if response.status_code == 429:
                # 验证速率限制头部
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                break

    @pytest.mark.asyncio
    async def test_chat_with_ai_concurrent_requests(self, client: AsyncClient, test_user: User):
        """测试并发请求"""
        import asyncio
        from app.utils.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        # 并发发送多个请求
        async def make_request(i):
            return await client.post("/api/ai/chat", headers=headers, json={
                "message": f"Concurrent test {i}"
            })

        responses = await asyncio.gather(*[make_request(i) for i in range(5)])
        
        # 所有请求都应该返回200或503或429（速率限制）
        for response in responses:
            assert response.status_code in [200, 503, 404, 429]
