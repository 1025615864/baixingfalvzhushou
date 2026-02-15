"""微信服务测试用例"""
import os
import sys
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

# 添加 backend 目录到 sys.path
backend_path = os.path.dirname(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.wechat import (
    WeChatConfig,
    WeChatAuth,
    WeChatMessageService,
    WeChatService,
    wechat_service,
    wechat_login,
    send_wechat_message,
)


class TestWeChatConfig:
    """微信配置测试"""

    def test_configure_mini_program(self):
        """测试配置小程序"""
        config = WeChatConfig()
        result = config.configure(
            platform="mini_program",
            app_id="wx_test_app_id",
            app_secret="wx_test_secret",
            mch_id="wx_test_mch_id",
            mch_key="wx_test_mch_key",
        )

        assert result["platform"] == "mini_program"
        assert result["app_id"] == "wx_test_app_id"
        assert result["configured"] is True

        stored = config.get_config("mini_program")
        assert stored["app_id"] == "wx_test_app_id"
        assert stored["mch_id"] == "wx_test_mch_id"
        assert stored["configured"] is True

    def test_configure_public(self):
        """测试配置公众号"""
        config = WeChatConfig()
        result = config.configure(
            platform="public",
            app_id="wx_public_app_id",
            app_secret="wx_public_secret",
        )

        assert result["platform"] == "public"
        assert result["app_id"] == "wx_public_app_id"
        assert result["configured"] is True

    def test_get_config_unconfigured(self):
        """测试获取未配置的平台"""
        config = WeChatConfig()
        result = config.get_config("unknown_platform")

        assert result == {}

    def test_get_config_after_configure(self):
        """测试配置后获取"""
        config = WeChatConfig()
        config.configure(
            platform="mini_program",
            app_id="test_id",
            app_secret="test_secret",
        )

        result = config.get_config("mini_program")
        assert result["app_id"] == "test_id"
        assert result["app_secret"] == "test_secret"


class TestWeChatAuth:
    """微信认证测试"""

    def test_code_to_session_mini_program(self):
        """测试小程序code换session"""
        auth = WeChatAuth()
        result = auth.code_to_session(
            platform="mini_program",
            code="test_code_12345678",
        )

        assert "openid" in result
        assert "session_key" in result
        assert "access_token" in result
        assert result["expires_in"] == 7200
        assert result["openid"].startswith("openid_mini_program_")
        assert result["session_key"].startswith("session_mini_program_")

    def test_code_to_session_public(self):
        """测试公众号code换session"""
        auth = WeChatAuth()
        result = auth.code_to_session(
            platform="public",
            code="public_code_87654321",
        )

        assert "openid" in result
        assert result["openid"].startswith("openid_public_")

    def test_bind_wechat(self):
        """测试绑定微信"""
        auth = WeChatAuth()
        result = auth.bind_wechat(
            user_id=12345,
            platform="mini_program",
            openid="test_openid_123",
        )

        assert result["bound"] is True
        assert result["user_id"] == 12345
        assert result["platform"] == "mini_program"

    def test_get_user_by_openid_exists(self):
        """测试获取已绑定的用户"""
        auth = WeChatAuth()
        auth.bind_wechat(
            user_id=12345,
            platform="mini_program",
            openid="test_openid_456",
        )

        result = auth.get_user_by_openid(
            platform="mini_program",
            openid="test_openid_456",
        )

        assert result is not None
        assert result["user_id"] == 12345
        assert result["openid"] == "test_openid_456"

    def test_get_user_by_openid_not_exists(self):
        """测试获取未绑定的用户"""
        auth = WeChatAuth()
        result = auth.get_user_by_openid(
            platform="mini_program",
            openid="nonexistent_openid",
        )

        assert result is None


class TestWeChatMessageService:
    """微信消息服务测试"""

    def test_register_template(self):
        """测试注册模板"""
        service = WeChatMessageService()
        result = service.register_template(
            template_id="test_template_001",
            name="测试模板",
            content="测试内容 {{keyword}}",
            example="测试示例",
        )

        assert result["template_id"] == "test_template_001"
        assert result["name"] == "测试模板"
        assert result["registered"] is True

    def test_send_message_success(self):
        """测试发送消息成功"""
        service = WeChatMessageService()
        service.register_template(
            template_id="test_template_001",
            name="测试模板",
            content="测试内容 {{keyword}}",
            example="测试示例",
        )

        result = service.send_message(
            to_user="test_openid",
            template_id="test_template_001",
            data={"keyword": {"value": "测试数据"}},
            page="pages/index/index",
        )

        assert result["success"] is True
        assert "message_id" in result
        assert result["status"] == "sent"

    def test_send_message_template_not_found(self):
        """测试发送消息-模板不存在"""
        service = WeChatMessageService()

        result = service.send_message(
            to_user="test_openid",
            template_id="nonexistent_template",
            data={"keyword": {"value": "测试数据"}},
        )

        assert result["success"] is False
        assert result["error"] == "模板不存在"

    def test_get_message_status_exists(self):
        """测试获取消息状态-存在"""
        service = WeChatMessageService()
        service.register_template(
            template_id="test_template_001",
            name="测试模板",
            content="测试内容",
            example="测试示例",
        )
        send_result = service.send_message(
            to_user="test_openid",
            template_id="test_template_001",
            data={"keyword": {"value": "测试数据"}},
        )

        result = service.get_message_status(send_result["message_id"])

        assert "message_id" in result
        assert result["status"] == "sent"
        assert "sent_at" in result

    def test_get_message_status_not_exists(self):
        """测试获取消息状态-不存在"""
        service = WeChatMessageService()

        result = service.get_message_status("nonexistent_msg_id")

        assert result["error"] == "消息不存在"
        assert result["message_id"] == "nonexistent_msg_id"

    def test_list_templates(self):
        """测试列出模板"""
        service = WeChatMessageService()
        service.register_template(
            template_id="template_001",
            name="模板1",
            content="内容1",
            example="示例1",
        )
        service.register_template(
            template_id="template_002",
            name="模板2",
            content="内容2",
            example="示例2",
        )

        result = service.list_templates()

        assert len(result) == 2
        assert result[0]["template_id"] == "template_001"
        assert result[1]["template_id"] == "template_002"


class TestWeChatService:
    """微信服务测试"""

    def test_configure_platform(self):
        """测试配置平台"""
        service = WeChatService()
        result = service.configure_platform(
            platform="mini_program",
            app_id="test_app_id",
            app_secret="test_secret",
            mch_id="test_mch_id",
            mch_key="test_mch_key",
        )

        assert result["platform"] == "mini_program"
        assert result["app_id"] == "test_app_id"
        assert result["configured"] is True

    @pytest.mark.asyncio
    async def test_login(self):
        """测试微信登录"""
        service = WeChatService()
        result = await service.login(
            platform="mini_program",
            code="test_code_12345678",
        )

        assert result["success"] is True
        assert "openid" in result
        assert "session_key" in result
        assert "access_token" in result

    @pytest.mark.asyncio
    async def test_bind_account(self):
        """测试绑定账号"""
        service = WeChatService()
        result = await service.bind_account(
            user_id=12345,
            platform="mini_program",
            openid="test_openid_789",
        )

        assert result["bound"] is True
        assert result["user_id"] == 12345

    @pytest.mark.asyncio
    async def test_send_template_message(self):
        """测试发送模板消息"""
        service = WeChatService()
        service.configure_platform(
            platform="mini_program",
            app_id="test_app_id",
            app_secret="test_secret",
        )
        # 先注册模板
        service._message.register_template(
            template_id="test_template",
            name="测试模板",
            content="测试内容 {{keyword}}",
            example="测试示例",
        )

        result = await service.send_template_message(
            to_openid="test_openid",
            template_id="test_template",
            data={"keyword": {"value": "测试数据"}},
        )

        assert result["success"] is True
        assert "message_id" in result

    def test_register_default_templates(self):
        """测试注册默认模板"""
        service = WeChatService()
        results = service.register_default_templates()

        assert len(results) == 5
        assert results[0]["template_id"] == "consult_reminder"
        assert results[1]["template_id"] == "appointment_reminder"
        assert results[2]["template_id"] == "document_ready"
        assert results[3]["template_id"] == "payment_success"
        assert results[4]["template_id"] == "system_notification"

    @pytest.mark.asyncio
    async def test_get_login_url(self):
        """测试获取网页授权登录URL"""
        service = WeChatService()
        service.configure_platform(
            platform="public",
            app_id="public_app_id",
            app_secret="public_secret",
        )

        result = await service.get_login_url(
            redirect_uri="https://example.com/callback",
        )

        assert "url" in result
        assert "state" in result
        assert result["url"].startswith("https://open.weixin.qq.com")
        assert "public_app_id" in result["url"]
        assert "example.com/callback" in result["url"]


class TestWeChatConvenienceFunctions:
    """微信便捷函数测试"""

    @pytest.mark.asyncio
    async def test_wechat_login_function(self):
        """测试便捷函数-微信登录"""
        result = await wechat_login(
            platform="mini_program",
            code="convenience_test_code",
        )

        assert result["success"] is True
        assert "openid" in result

    @pytest.mark.asyncio
    async def test_send_wechat_message_function(self):
        """测试便捷函数-发送模板消息"""
        # 先注册模板到全局服务
        wechat_service._message.register_template(
            template_id="convenience_template",
            name="便捷模板",
            content="便捷内容",
            example="便捷示例",
        )

        result = await send_wechat_message(
            to_openid="convenience_openid",
            template_id="convenience_template",
            data={"keyword": {"value": "便捷测试数据"}},
        )

        assert result["success"] is True
        assert "message_id" in result


class TestWeChatEdgeCases:
    """微信服务边界条件测试"""

    def test_empty_configure(self):
        """测试空配置"""
        config = WeChatConfig()
        result = config.configure(
            platform="empty_test",
            app_id="",
            app_secret="",
        )

        assert result["platform"] == "empty_test"
        assert result["app_id"] == ""

    def test_multiple_platform_config(self):
        """测试多平台配置"""
        config = WeChatConfig()
        config.configure(
            platform="mini_program",
            app_id="mp_id",
            app_secret="mp_secret",
        )
        config.configure(
            platform="public",
            app_id="pub_id",
            app_secret="pub_secret",
        )

        mp_config = config.get_config("mini_program")
        pub_config = config.get_config("public")

        assert mp_config["app_id"] == "mp_id"
        assert pub_config["app_id"] == "pub_id"

    def test_message_with_empty_data(self):
        """测试发送空数据消息"""
        service = WeChatMessageService()
        service.register_template(
            template_id="empty_data_template",
            name="空数据模板",
            content="无数据",
            example="无示例",
        )

        result = service.send_message(
            to_user="empty_data_openid",
            template_id="empty_data_template",
            data={},
        )

        assert result["success"] is True

    def test_message_without_page(self):
        """测试不传page参数"""
        service = WeChatMessageService()
        service.register_template(
            template_id="no_page_template",
            name="无页面模板",
            content="无页面",
            example="无示例",
        )

        result = service.send_message(
            to_user="no_page_openid",
            template_id="no_page_template",
            data={"keyword": {"value": "测试"}},
        )

        assert result["success"] is True
        assert "page" not in result or result.get("page") is None

    def test_auth_multiple_sessions(self):
        """测试多会话存储"""
        auth = WeChatAuth()
        result1 = auth.code_to_session(
            platform="mini_program",
            code="session_code_1",
        )
        result2 = auth.code_to_session(
            platform="mini_program",
            code="session_code_2",
        )

        assert result1["access_token"] != result2["access_token"]
        assert len(auth._tokens) == 2

    def test_bind_multiple_users(self):
        """测试多用户绑定"""
        auth = WeChatAuth()
        auth.bind_wechat(
            user_id=1001,
            platform="mini_program",
            openid="openid_1001",
        )
        auth.bind_wechat(
            user_id=1002,
            platform="mini_program",
            openid="openid_1002",
        )

        user1 = auth.get_user_by_openid("mini_program", "openid_1001")
        user2 = auth.get_user_by_openid("mini_program", "openid_1002")

        assert user1["user_id"] == 1001
        assert user2["user_id"] == 1002
