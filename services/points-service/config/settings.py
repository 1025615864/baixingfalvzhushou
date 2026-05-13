"""积分服务配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class PointsSettings(BaseSettings):
    service_name: str = "points-service"
    service_port: int = 8012
    database_url: str = os.getenv("POINTS_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/points")
    db_pool_size: int = 20
    db_max_overflow: int = 30
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> PointsSettings:
    return PointsSettings()
