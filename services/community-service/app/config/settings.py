"""社区服务配置"""
import os
from typing import Optional


class Settings:
    """社区服务配置"""
    
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./community_service.db"
    )
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
