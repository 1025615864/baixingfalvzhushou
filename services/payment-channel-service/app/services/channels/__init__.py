from typing import Dict

from .base import PaymentChannelAdapter
from .alipay_adapter import AlipayAdapter
from .wechat_adapter import WechatAdapter

_adapters: Dict[str, PaymentChannelAdapter] = {}


def register_adapter(name: str, adapter: PaymentChannelAdapter) -> None:
    _adapters[name] = adapter


def get_adapter(provider: str) -> PaymentChannelAdapter:
    adapter = _adapters.get(provider)
    if not adapter:
        raise ValueError(f"Unknown payment provider: {provider}")
    return adapter


def init_adapters(settings) -> None:
    if settings.alipay_app_id:
        alipay = AlipayAdapter(
            app_id=settings.alipay_app_id,
            private_key=settings.alipay_private_key,
            public_key=settings.alipay_public_key,
            gateway_url=settings.alipay_gateway_url,
            notify_url=settings.alipay_notify_url,
        )
        register_adapter("alipay", alipay)

    if settings.wechatpay_mch_id:
        wechat = WechatAdapter(
            mch_id=settings.wechatpay_mch_id,
            private_key=settings.wechatpay_private_key,
            api_v3_key=settings.wechatpay_api_v3_key,
            app_id=getattr(settings, "wechatpay_app_id", ""),
            cert_path=getattr(settings, "wechatpay_cert_path", ""),
            notify_url=getattr(settings, "wechatpay_notify_url", ""),
        )
        register_adapter("wechat", wechat)


__all__ = [
    "PaymentChannelAdapter",
    "AlipayAdapter",
    "WechatAdapter",
    "register_adapter",
    "get_adapter",
    "init_adapters",
]
