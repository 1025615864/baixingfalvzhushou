"""搜索服务配置"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "search-service"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/search_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    DEBUG: bool = False

    COMMUNITY_SERVICE_URL: str = "http://localhost:8003"
    LEGAL_SERVICE_URL: str = "http://localhost:8004"
    NEWS_SERVICE_URL: str = "http://localhost:8007"
    KNOWLEDGE_SERVICE_URL: str = "http://localhost:8006"

    SEARCH_CACHE_TTL: int = 60
    HOT_SEARCH_CACHE_TTL: int = 300
    SERVICE_TIMEOUT: float = 10.0

    CORS_ORIGINS: str = "*"

    class Config:
        env_file = ".env"


settings = Settings()
