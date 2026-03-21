"""账务服务配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class AccountingSettings(BaseSettings):
    """账务服务配置"""

    service_name: str = "payment-accounting-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8003

    database_url: str = os.getenv(
        "ACCOUNTING_DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/accounting"
    )
    db_pool_size: int = 20
    db_max_overflow: int = 30

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> AccountingSettings:
    return AccountingSettings()
