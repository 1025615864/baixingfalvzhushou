"""短信服务抽象层

提供多厂商短信服务切换和降级功能。
"""
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SMSProvider(str, Enum):
    """短信服务提供商"""

    ALIYUN = "aliyun"
    TENCENT = "tencent"
    HUAWEI = "huawei"
    MOCK = "mock"


class SMSResult:
    """短信发送结果"""

    def __init__(
        self,
        success: bool,
        provider: str,
        message_id: str | None = None,
        error: str | None = None,
    ):
        self.success = success
        self.provider = provider
        self.message_id = message_id
        self.error = error

    def __repr__(self) -> str:
        return f"SMSResult(success={
            self.success}, provider={
            self.provider}, message_id={
            self.message_id})"


class BaseSMSProvider(ABC):
    """短信服务基类"""

    def __init__(self, provider: SMSProvider):
        self.provider = provider
        self.name = provider.value

    @abstractmethod
    async def send_sms(
        self,
        phone: str,
        template_code: str,
        template_params: dict[str, Any],
    ) -> SMSResult:
        """发送短信

        Args:
            phone: 手机号
            template_code: 模板代码
            template_params: 模板参数

        Returns:
            发送结果
        """
        pass

    @abstractmethod
    async def verify_connection(self) -> bool:
        """验证连接

        Returns:
            是否连接成功
        """
        pass


class MockSMSProvider(BaseSMSProvider):
    """Mock 短信服务（用于开发测试）"""

    def __init__(self):
        super().__init__(SMSProvider.MOCK)
        self._sent_messages: list[dict[str, Any]] = []

    async def send_sms(
        self,
        phone: str,
        template_code: str,
        template_params: dict[str, Any],
    ) -> SMSResult:
        """发送 Mock 短信"""
        message_id = f"mock_{len(self._sent_messages) + 1}"
        self._sent_messages.append({
            "phone": phone,
            "template_code": template_code,
            "params": template_params,
            "message_id": message_id,
        })
        logger.info(
            f"[MOCK SMS] Phone: {phone}, Template: {template_code}, Params: {template_params}")
        return SMSResult(
            success=True,
            provider=self.name,
            message_id=message_id,
        )

    async def verify_connection(self) -> bool:
        return True

    def get_sent_messages(self) -> list[dict[str, Any]]:
        return self._sent_messages.copy()

    def clear_messages(self) -> None:
        self._sent_messages.clear()


class SMSProviderManager:
    """短信服务管理器"""

    _instance: "SMSProviderManager | None" = None

    def __init__(self):
        self._providers: dict[SMSProvider, BaseSMSProvider] = {}
        self._current_provider: SMSProvider | None = None
        self._fallback_provider: SMSProvider = SMSProvider.MOCK
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """初始化所有提供商"""
        self._providers[SMSProvider.MOCK] = MockSMSProvider()
        self._current_provider = SMSProvider.MOCK

    def register_provider(self, provider: BaseSMSProvider) -> None:
        """注册短信服务提供商"""
        self._providers[provider.provider] = provider
        logger.info(f"Registered SMS provider: {provider.name}")

    def set_primary_provider(self, provider: SMSProvider) -> bool:
        """设置主服务提供商

        Args:
            provider: 提供商类型

        Returns:
            是否设置成功
        """
        if provider not in self._providers:
            logger.warning(f"Provider {provider} not registered")
            return False

        self._current_provider = provider
        logger.info(f"Primary SMS provider set to: {provider.value}")
        return True

    def set_fallback_provider(self, provider: SMSProvider) -> None:
        """设置降级服务提供商"""
        self._fallback_provider = provider
        logger.info(f"Fallback SMS provider set to: {provider.value}")

    async def send_sms(
        self,
        phone: str,
        template_code: str,
        template_params: dict[str, Any],
        provider: SMSProvider | None = None,
    ) -> SMSResult:
        """发送短信

        Args:
            phone: 手机号
            template_code: 模板代码
            template_params: 模板参数
            provider: 指定提供商（可选）

        Returns:
            发送结果
        """
        target_provider = provider or self._current_provider

        if target_provider is None:
            target_provider = self._fallback_provider

        provider_instance = self._providers.get(target_provider)

        if provider_instance is None:
            provider_instance = self._providers.get(self._fallback_provider)

        if provider_instance is None:
            return SMSResult(
                success=False,
                provider="none",
                error="No SMS provider available",
            )

        try:
            result = await provider_instance.send_sms(
                phone=phone,
                template_code=template_code,
                template_params=template_params,
            )
            return result
        except Exception as e:
            logger.error(f"SMS send failed with {target_provider}: {e}")

            if target_provider != self._fallback_provider:
                logger.info("Falling back to fallback provider")
                fallback_instance = self._providers.get(
                    self._fallback_provider)
                if fallback_instance:
                    try:
                        return await fallback_instance.send_sms(
                            phone=phone,
                            template_code=template_code,
                            template_params=template_params,
                        )
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback SMS also failed: {fallback_error}")

            return SMSResult(
                success=False,
                provider=target_provider.value if target_provider else "unknown",
                error=str(e),
            )

    async def verify_all_providers(self) -> dict[str, bool]:
        """验证所有提供商连接

        Returns:
            各提供商的验证结果
        """
        results: dict[str, bool] = {}
        for provider_type, provider in self._providers.items():
            try:
                results[provider_type.value] = await provider.verify_connection()
            except Exception as e:
                logger.error(
                    f"Provider {provider_type} verification failed: {e}")
                results[provider_type.value] = False
        return results

    def get_current_provider(self) -> SMSProvider | None:
        return self._current_provider

    def get_provider_status(self) -> dict[str, Any]:
        return {
            "current": self._current_provider.value if self._current_provider else None,
            "fallback": self._fallback_provider.value,
            "available": list(
                self._providers.keys()),
        }


# 单例实例
sms_manager = SMSProviderManager()


async def send_sms(
    phone: str,
    template_code: str,
    template_params: dict[str, Any],
    provider: SMSProvider | None = None,
) -> SMSResult:
    """便捷函数：发送短信

    Args:
        phone: 手机号
        template_code: 模板代码
        template_params: 模板参数
        provider: 指定提供商（可选）

    Returns:
        发送结果
    """
    return await sms_manager.send_sms(
        phone=phone,
        template_code=template_code,
        template_params=template_params,
        provider=provider,
    )


def get_sms_status() -> dict[str, Any]:
    """获取短信服务状态"""
    return sms_manager.get_provider_status()
