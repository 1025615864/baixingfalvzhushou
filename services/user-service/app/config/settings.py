"""用户服务配置"""
import os
import secrets
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class UserServiceSettings(BaseSettings):
    """用户服务配置"""

    service_name: str = "user-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8001

    database_url: str = os.getenv(
        "USER_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5433/user_service"
    )
    db_pool_size: int = 20
    db_max_overflow: int = 30

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:16379/0")
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")

    jwt_algorithm: str = "HS256"
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        secrets.token_urlsafe(32)
    )
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_enabled: bool = os.getenv("ENABLE_KAFKA", "false").lower() in {"1", "true", "yes"}

    cors_allowed_origins: str = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    )

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> UserServiceSettings:
    return UserServiceSettings()
