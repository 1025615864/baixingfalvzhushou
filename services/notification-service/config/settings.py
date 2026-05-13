"""通知服务配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class NotificationSettings(BaseSettings):
    service_name: str = "notification-service"
    service_port: int = 8011
    database_url: str = os.getenv("NOTIFICATION_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/notification")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> NotificationSettings:
    return NotificationSettings()
