"""支付通道服务配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class PaymentChannelSettings(BaseSettings):
    """支付通道服务配置"""

    service_name: str = "payment-channel-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8002

    database_url: str = os.getenv(
        "PAYMENT_CHANNEL_DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/payment_channel"
    )
    db_pool_size: int = 20
    db_max_overflow: int = 30

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # 支付通道配置
    alipay_app_id: str = os.getenv("ALIPAY_APP_ID", "")
    alipay_private_key: str = os.getenv("ALIPAY_PRIVATE_KEY", "")
    alipay_public_key: str = os.getenv("ALIPAY_PUBLIC_KEY", "")
    alipay_gateway_url: str = "https://openapi.alipay.com/gateway.do"
    alipay_notify_url: str = ""

    wechatpay_mch_id: str = os.getenv("WECHATPAY_MCH_ID", "")
    wechatpay_private_key: str = os.getenv("WECHATPAY_PRIVATE_KEY", "")
    wechatpay_api_v3_key: str = os.getenv("WECHATPAY_API_V3_KEY", "")
    wechatpay_app_id: str = os.getenv("WECHATPAY_APP_ID", "")
    wechatpay_cert_path: str = os.getenv("WECHATPAY_CERT_PATH", "")
    wechatpay_notify_url: str = os.getenv("WECHATPAY_NOTIFY_URL", "")

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> PaymentChannelSettings:
    return PaymentChannelSettings()
