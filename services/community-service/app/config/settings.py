"""社区服务配置"""
import os
from typing import Optional

try:
    from services.common.config import Config, config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    config = None


class Settings:
    """社区服务配置"""

    def __init__(self):
        if CONFIG_AVAILABLE and config.is_initialized():
            self._load_from_config_manager()
        else:
            self._load_from_env()

    def _load_from_config_manager(self):
        self.database_url = Config.get("database.url", os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./community_service.db"
        ))
        self.db_pool_size = Config.get("database.pool_size", 10)
        self.db_max_overflow = Config.get("database.max_overflow", 20)
        self.service_name = Config.get("service.name", "community-service")
        self.service_host = Config.get("service.host", "0.0.0.0")
        self.service_port = Config.get("service.port", 8007)

    def _load_from_env(self):
        self.database_url = os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./community_service.db"
        )
        self.db_pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.service_name = os.getenv("SERVICE_NAME", "community-service")
        self.service_host = os.getenv("SERVICE_HOST", "0.0.0.0")
        self.service_port = int(os.getenv("SERVICE_PORT", "8007"))


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
