"""推荐服务配置"""
import os
from typing import Optional


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./recommendation_service.db")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    
    news_service_url: str = os.getenv("NEWS_SERVICE_URL", "http://localhost:8006")
    community_service_url: str = os.getenv("COMMUNITY_SERVICE_URL", "http://localhost:8007")
    user_service_url: str = os.getenv("USER_SERVICE_URL", "http://localhost:8001")


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
