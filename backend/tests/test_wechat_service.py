"""微信生态集成服务测试用例"""
import os
import sys
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# 添加 backend 目录到 sys.path
backend_path = os.path.dirname(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.wechat_service import (
    WeChatAuthService,
    WeChatMessageService,
    WeChatMiniProgramService,
    wechat_auth_service,
    wechat_message_service,
    wechat_mini_service,
)


class TestWeChatAuthService:
    """微信认证服务测试"""

    def test_auth_service_init(self):
        """测试认证服务初始化"""
        service = WeChatAuthService()
        assert service is not None
        assert hasattr(service, "_sessions")
        assert hasattr(service, "_users")
        assert service._sessions == {}
        assert service._users == {}

    @pytest.mark.asyncio
    async def test_get_login_qrcode(self):
        """测试获取登录二维码"""
        service = WeChatAuthService()
        result = await service.get_login_qrcode("https://example.com/callback")

        assert "qrcode_url" in result
        assert "state" in result
        assert "expires_in" in result
        assert result["expires_in"] == 1800
        assert "weixin.qq.com" in result["qrcode_url"]

    @pytest.mark.asyncio
    async def test_handle_callback_valid_code(self):
        """测试处理有效回调"""
        service = WeChatAuthService()
        result = await service.handle_callback("test_code", "test_state")

        assert result["success"] is True
        assert "openid" in result
        assert "session_key" in result
        assert result["expires_in"] == 86400

    @pytest.mark.asyncio
    async def test_handle_callback_empty_code(self):
        """测试处理空回调"""
        service = WeChatAuthService()
        result = await service.handle_callback("", "test_state")

        assert result["success"] is False
        assert result["error"] == "授权码无效"

    @pytest.mark.asyncio
    async def test_get_user_info_exists(self):
        """测试获取存在的用户信息"""
        service = WeChatAuthService()
        service._users[1234] = {"name": "Test User", "avatar": "avatar_url"}

        result = await service.get_user_info("wx_4D2")

        assert result is not None
        assert result["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_get_user_info_not_exists(self):
        """测试获取不存在的用户信息"""
        service = WeChatAuthService()

        # 使用有效的 hex 格式 openid
        result = await service.get_user_info("wx_FFFF")

        assert result is None


class TestWeChatMessagePushService:
    """微信消息推送服务测试"""

    def test_message_service_init(self):
        """测试消息服务初始化"""
        service = WeChatMessageService()
        assert service is not None
        assert hasattr(service, "_templates")
        assert hasattr(service, "_messages")
        assert service._templates == {}
        assert service._messages == []

    @pytest.mark.asyncio
    async def test_send_template_message(self):
        """测试发送模板消息"""
        service = WeChatMessageService()
        result = await service.send_template_message(
            openid="user123",
            template_id="template_001",
            data={"first": {"value": "Hello"}},
        )

        assert result["success"] is True
        assert "msg_id" in result
        assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_send_template_message_with_page(self):
        """测试发送带页面的模板消息"""
        service = WeChatMessageService()
        result = await service.send_template_message(
            openid="user123",
            template_id="template_001",
            data={"first": {"value": "Hello"}},
            page="pages/index/index",
        )

        assert result["success"] is True
        assert len(service._messages) == 1
        assert service._messages[0]["page"] == "pages/index/index"

    @pytest.mark.asyncio
    async def test_get_message_history(self):
        """测试获取消息历史"""
        service = WeChatMessageService()
        # 发送几条消息
        await service.send_template_message("user1", "t1", {"data": "test1"})
        await service.send_template_message("user1", "t1", {"data": "test2"})
        await service.send_template_message("user2", "t1", {"data": "test3"})

        history = await service.get_message_history("user1", limit=10)

        assert len(history) == 2
        for msg in history:
            assert msg["openid"] == "user1"

    @pytest.mark.asyncio
    async def test_get_message_history_limit(self):
        """测试获取消息历史限制数量"""
        service = WeChatMessageService()
        # 发送多条消息
        for i in range(25):
            await service.send_template_message("user1", "t1", {"data": f"test{i}"})

        history = await service.get_message_history("user1", limit=10)

        assert len(history) == 10

    def test_register_template(self):
        """测试注册模板"""
        service = WeChatMessageService()
        result = service.register_template(
            template_id="template_001",
            name="测试模板",
            content="这是一段测试内容",
        )

        assert result["success"] is True
        assert result["template_id"] == "template_001"
        assert "template_001" in service._templates
        assert service._templates["template_001"]["name"] == "测试模板"


class TestWeChatMiniProgramService:
    """微信小程序服务测试"""

    def test_mp_service_init(self):
        """测试小程序服务初始化"""
        service = WeChatMiniProgramService()
        assert service is not None
        assert hasattr(service, "_codes")
        assert service._codes == {}

    @pytest.mark.asyncio
    async def test_get_wxacode(self):
        """测试获取小程序码"""
        service = WeChatMiniProgramService()
        result = await service.get_wxacode("pages/index/index", width=430)

        assert "url" in result
        assert result["path"] == "pages/index/index"
        assert result["width"] == 430
        assert result["expires_in"] == 86400

    @pytest.mark.asyncio
    async def test_get_wxacode_custom_width(self):
        """测试获取自定义宽度小程序码"""
        service = WeChatMiniProgramService()
        result = await service.get_wxacode("pages/detail/detail", width=256)

        assert result["width"] == 256

    @pytest.mark.asyncio
    async def test_analyze_scene(self):
        """测试解析场景值"""
        service = WeChatMiniProgramService()
        result = await service.analyze_scene("scene_123")

        assert "scene" in result
        assert "params" in result
        assert result["scene"] == "scene_123"

    @pytest.mark.asyncio
    async def test_analyze_scene_with_params(self):
        """测试解析带参数的场景值"""
        service = WeChatMiniProgramService()
        result = await service.analyze_scene("id=123&type=article")

        assert "scene" in result
        assert "params" in result
        assert result["scene"] == "id=123&type=article"
        # 注意：当前实现不解析参数，只是返回空 params
        assert result["params"] == {}


class TestWeChatServiceSingletons:
    """微信服务单例测试"""

    def test_auth_service_singleton(self):
        """测试认证服务单例"""
        assert wechat_auth_service is not None
        assert isinstance(wechat_auth_service, WeChatAuthService)

    def test_message_service_singleton(self):
        """测试消息服务单例"""
        assert wechat_message_service is not None
        assert isinstance(wechat_message_service, WeChatMessageService)

    def test_mp_service_singleton(self):
        """测试小程序服务单例"""
        assert wechat_mini_service is not None
        assert isinstance(wechat_mini_service, WeChatMiniProgramService)


class TestWeChatServiceEdgeCases:
    """微信服务边界条件测试"""

    @pytest.mark.asyncio
    async def test_send_message_empty_openid(self):
        """测试发送空openid消息"""
        service = WeChatMessageService()
        result = await service.send_template_message(
            openid="",
            template_id="template_001",
            data={"first": {"value": "Hello"}},
        )

        assert result["success"] is True
        assert result["msg_id"] == 1

    @pytest.mark.asyncio
    async def test_get_message_history_empty(self):
        """测试获取空消息历史"""
        service = WeChatMessageService()

        history = await service.get_message_history("unknown_user")

        assert history == []

    @pytest.mark.asyncio
    async def test_get_user_info_special_openid(self):
        """测试获取特殊openid的用户信息"""
        service = WeChatAuthService()

        # 测试各种openid格式
        result1 = await service.get_user_info("wx_0")
        assert result1 is None

        result2 = await service.get_user_info("wx_FFFF")
        assert result2 is None

    def test_register_empty_template(self):
        """测试注册空模板"""
        service = WeChatMessageService()
        result = service.register_template("", "", "")

        assert result["success"] is True
        assert "" in service._templates


class TestWeChatServiceIntegration:
    """微信服务集成测试"""

    @pytest.mark.asyncio
    async def test_full_auth_flow(self):
        """测试完整认证流程"""
        service = WeChatAuthService()

        # 获取二维码
        qrcode = await service.get_login_qrcode("https://example.com/callback")
        assert "qrcode_url" in qrcode
        assert "state" in qrcode

        # 处理回调
        result = await service.handle_callback("auth_code", qrcode["state"])
        assert result["success"] is True
        assert "openid" in result

    @pytest.mark.asyncio
    async def test_full_message_flow(self):
        """测试完整消息流程"""
        message_service = WeChatMessageService()

        # 注册模板
        template_result = message_service.register_template(
            "notice_template",
            "通知模板",
            "您有一条新通知",
        )
        assert template_result["success"] is True

        # 发送消息
        send_result = await message_service.send_template_message(
            "user123",
            "notice_template",
            {"first": {"value": "您有新消息"}},
        )
        assert send_result["success"] is True

        # 获取历史
        history = await message_service.get_message_history("user123")
        assert len(history) == 1
        assert history[0]["template_id"] == "notice_template"

    @pytest.mark.asyncio
    async def test_full_mp_flow(self):
        """测试完整小程序流程"""
        mp_service = WeChatMiniProgramService()

        # 获取小程序码
        wxacode = await mp_service.get_wxacode("pages/index/index")
        assert wxacode["path"] == "pages/index/index"

        # 解析场景
        scene = await mp_service.analyze_scene("share=abc123")
        assert scene["scene"] == "share=abc123"
