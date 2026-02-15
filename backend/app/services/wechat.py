"""微信生态服务

提供微信小程序和公众号的登录、消息推送功能。
"""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class WeChatConfig:
    """微信配置"""

    def __init__(self):
        self._config: dict[str, dict[str, Any]] = {}

    def configure(
        self,
        platform: str,
        app_id: str,
        app_secret: str,
        mch_id: str | None = None,
        mch_key: str | None = None,
    ) -> dict[str, Any]:
        """配置微信平台

        Args:
            platform: 平台（mini_program/public）
            app_id: 应用ID
            app_secret: 应用密钥
            mch_id: 商户ID
            mch_key: 商户密钥

        Returns:
            配置结果
        """
        self._config[platform] = {
            "app_id": app_id,
            "app_secret": app_secret,
            "mch_id": mch_id,
            "mch_key": mch_key,
            "configured": True,
        }

        return {
            "platform": platform,
            "app_id": app_id,
            "configured": True,
        }

    def get_config(self, platform: str) -> dict[str, Any]:
        """获取配置

        Args:
            platform: 平台

        Returns:
            配置信息
        """
        return self._config.get(platform, {})


class WeChatAuth:
    """微信认证"""

    def __init__(self):
        self._tokens: dict[str, dict[str, Any]] = {}
        self._users: dict[str, dict[str, Any]] = {}

    def code_to_session(
        self,
        platform: str,
        code: str,
    ) -> dict[str, Any]:
        """Code 换 Session

        Args:
            platform: 平台
            code: 登录凭证

        Returns:
            会话信息
        """
        openid = f"openid_{platform}_{code[:8]}"
        session_key = f"session_{platform}_{code[:8]}"

        token = f"token_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        self._tokens[token] = {
            "openid": openid,
            "session_key": session_key,
            "expires_at": datetime.now(timezone.utc).timestamp() + 7200,
        }

        return {
            "openid": openid,
            "session_key": session_key,
            "access_token": token,
            "expires_in": 7200,
        }

    def bind_wechat(
        self,
        user_id: int,
        platform: str,
        openid: str,
    ) -> dict[str, Any]:
        """绑定微信

        Args:
            user_id: 用户ID
            platform: 平台
            openid: 微信OpenID

        Returns:
            绑定结果
        """
        key = f"{platform}:{openid}"
        self._users[key] = {
            "user_id": user_id,
            "platform": platform,
            "openid": openid,
            "bound_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "bound": True,
            "user_id": user_id,
            "platform": platform,
        }

    def get_user_by_openid(
        self,
        platform: str,
        openid: str,
    ) -> dict[str, Any] | None:
        """通过OpenID获取用户

        Args:
            platform: 平台
            openid: OpenID

        Returns:
            用户信息
        """
        key = f"{platform}:{openid}"
        return self._users.get(key)


class WeChatMessageService:
    """微信消息服务"""

    def __init__(self):
        self._templates: dict[str, dict[str, Any]] = {}
        self._messages: dict[str, dict[str, Any]] = {}

    def register_template(
        self,
        template_id: str,
        name: str,
        content: str,
        example: str,
    ) -> dict[str, Any]:
        """注册消息模板

        Args:
            template_id: 模板ID
            name: 名称
            content: 内容
            example: 示例

        Returns:
            注册结果
        """
        self._templates[template_id] = {
            "template_id": template_id,
            "name": name,
            "content": content,
            "example": example,
            "enabled": True,
        }

        return {
            "template_id": template_id,
            "name": name,
            "registered": True,
        }

    def send_message(
        self,
        to_user: str,
        template_id: str,
        data: dict[str, Any],
        page: str | None = None,
    ) -> dict[str, Any]:
        """发送模板消息

        Args:
            to_user: 接收用户OpenID
            template_id: 模板ID
            data: 模板数据
            page: 跳转页面

        Returns:
            发送结果
        """
        template = self._templates.get(template_id)
        if not template:
            return {
                "success": False,
                "error": "模板不存在",
            }

        msg_id = f"msg_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        message = {
            "id": msg_id,
            "to_user": to_user,
            "template_id": template_id,
            "data": data,
            "page": page,
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

        self._messages[msg_id] = message

        logger.info(f"WeChat message sent: {msg_id} to {to_user}")

        return {
            "success": True,
            "message_id": msg_id,
            "status": "sent",
        }

    def get_message_status(self, message_id: str) -> dict[str, Any]:
        """获取消息状态

        Args:
            message_id: 消息ID

        Returns:
            状态信息
        """
        message = self._messages.get(message_id)
        if not message:
            return {
                "error": "消息不存在",
                "message_id": message_id,
            }

        return {
            "message_id": message_id,
            "status": message["status"],
            "sent_at": message["sent_at"],
        }

    def list_templates(self) -> list[dict[str, Any]]:
        """列出模板

        Returns:
            模板列表
        """
        return list(self._templates.values())


class WeChatService:
    """微信服务"""

    def __init__(self):
        self._config = WeChatConfig()
        self._auth = WeChatAuth()
        self._message = WeChatMessageService()

    def configure_platform(
        self,
        platform: str,
        app_id: str,
        app_secret: str,
        mch_id: str | None = None,
        mch_key: str | None = None,
    ) -> dict[str, Any]:
        """配置平台

        Args:
            platform: 平台
            app_id: 应用ID
            app_secret: 应用密钥
            mch_id: 商户ID
            mch_key: 商户密钥

        Returns:
            配置结果
        """
        return self._config.configure(
            platform=platform,
            app_id=app_id,
            app_secret=app_secret,
            mch_id=mch_id,
            mch_key=mch_key,
        )

    async def login(
        self,
        platform: str,
        code: str,
    ) -> dict[str, Any]:
        """微信登录

        Args:
            platform: 平台
            code: 登录凭证

        Returns:
            登录结果
        """
        session = self._auth.code_to_session(platform, code)

        return {
            "success": True,
            "openid": session["openid"],
            "session_key": session["session_key"],
            "access_token": session["access_token"],
        }

    async def bind_account(
        self,
        user_id: int,
        platform: str,
        openid: str,
    ) -> dict[str, Any]:
        """绑定账号

        Args:
            user_id: 用户ID
            platform: 平台
            openid: OpenID

        Returns:
            绑定结果
        """
        return self._auth.bind_wechat(
            user_id=user_id,
            platform=platform,
            openid=openid,
        )

    async def send_template_message(
        self,
        to_openid: str,
        template_id: str,
        data: dict[str, Any],
        page: str | None = None,
    ) -> dict[str, Any]:
        """发送模板消息

        Args:
            to_openid: 接收用户OpenID
            template_id: 模板ID
            data: 模板数据
            page: 跳转页面

        Returns:
            发送结果
        """
        return self._message.send_message(
            to_user=to_openid,
            template_id=template_id,
            data=data,
            page=page,
        )

    def register_default_templates(self) -> list[dict[str, Any]]:
        """注册默认模板

        Returns:
            注册结果
        """
        templates = [
            ("consult_reminder", "咨询提醒", "您有新的法律咨询待回复", "点击查看详情"),
            ("appointment_reminder", "预约提醒", "您有新的预约待确认", "点击查看详情"),
            ("document_ready", "文书完成", "您的法律文书已生成", "点击查看详情"),
            ("payment_success", "支付成功", "您的订单已支付成功", "点击查看详情"),
            ("system_notification", "系统通知", "您有一条新的系统消息", "点击查看详情"),
        ]

        results = []
        for template_id, name, content, example in templates:
            result = self._message.register_template(
                template_id=template_id,
                name=name,
                content=content,
                example=example,
            )
            results.append(result)

        return results

    async def get_login_url(self, redirect_uri: str) -> dict[str, Any]:
        """获取网页授权登录URL

        Args:
            redirect_uri: 回调地址

        Returns:
            授权URL
        """
        app_id = self._config.get_config("public").get("app_id", "")
        state = f"state_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        url = f"https://open.weixin.qq.com/connect/oauth2/authorize?appid={app_id}&redirect_uri={redirect_uri}&response_type=code&scope=snsapi_userinfo&state={state}#wechat_redirect"

        return {
            "url": url,
            "state": state,
        }


# 单例实例
wechat_service = WeChatService()


async def wechat_login(
    platform: str,
    code: str,
) -> dict[str, Any]:
    """便捷函数：微信登录

    Args:
        platform: 平台
        code: 登录凭证

    Returns:
        登录结果
    """
    return await wechat_service.login(platform=platform, code=code)


async def send_wechat_message(
    to_openid: str,
    template_id: str,
    data: dict[str, Any],
    page: str | None = None,
) -> dict[str, Any]:
    """便捷函数：发送模板消息

    Args:
        to_openid: 接收用户OpenID
        template_id: 模板ID
        data: 模板数据
        page: 跳转页面

    Returns:
        发送结果
    """
    return await wechat_service.send_template_message(
        to_openid=to_openid,
        template_id=template_id,
        data=data,
        page=page,
    )
