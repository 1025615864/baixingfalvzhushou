"""用户服务配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class UserServiceSettings(BaseSettings):
    """用户服务配置"""

    # 服务配置
    service_name: str = "user-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8001

    # 数据库配置
    database_url: str = os.getenv(
        "USER_DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/user_service"
    )
    db_pool_size: int = 20
    db_max_overflow: int = 30

    # Redis 配置
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # JWT 配置
    jwt_rsa_private_key: str = ""
    jwt_rsa_public_key: str = ""
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Kafka 配置
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> UserServiceSettings:
    return UserServiceSettings()
