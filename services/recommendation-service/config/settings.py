"""推荐服务配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class RecommendationSettings(BaseSettings):
    service_name: str = "recommendation-service"
    service_port: int = 8010
    database_url: str = os.getenv("RECOMMENDATION_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/recommendation")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> RecommendationSettings:
    return RecommendationSettings()
