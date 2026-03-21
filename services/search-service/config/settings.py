"""搜索服务配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class SearchSettings(BaseSettings):
    service_name: str = "search-service"
    service_port: int = 8011
    database_url: str = os.getenv("SEARCH_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/search")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> SearchSettings:
    return SearchSettings()
