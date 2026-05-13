"""支付通道服务配置"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "payment-channel-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8002
    debug: bool = True

    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/payment_channel_service")
    db_pool_size: int = 20
    db_max_overflow: int = 30

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

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
        extra = "ignore"

    def get_cors_config(self):
        return {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }


_settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
