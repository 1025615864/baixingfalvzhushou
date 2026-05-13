import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class AccountingSettings(BaseSettings):
    service_name: str = "payment-accounting-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8014

    database_url: str = os.getenv(
        "ACCOUNTING_DATABASE_URL",
        os.getenv("DATABASE_URL", "")
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> AccountingSettings:
    settings = AccountingSettings()
    if not settings.database_url:
        raise ValueError(
            "ACCOUNTING_DATABASE_URL or DATABASE_URL environment variable must be set"
        )
    return settings
