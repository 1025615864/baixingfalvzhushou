"""通知服务配置"""
import os
from typing import Optional


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./notification_service.db")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    
    email_enabled: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    sms_enabled: bool = os.getenv("SMS_ENABLED", "false").lower() == "true"
    push_enabled: bool = os.getenv("PUSH_ENABLED", "false").lower() == "true"


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
