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
    legal_service_url: str = os.getenv("LEGAL_SERVICE_URL", "http://localhost:8008")

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    cache_ttl: int = int(os.getenv("RECOMMENDATION_CACHE_TTL", "300"))

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    kafka_enabled: bool = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}
    kafka_consumer_group: str = os.getenv("KAFKA_CONSUMER_GROUP_ID", "recommendation-service-events")

    http_timeout: float = float(os.getenv("HTTP_CLIENT_TIMEOUT", "10.0"))


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
