"""搜索服务配置"""
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "search-service"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    DEBUG: bool = False

    COMMUNITY_SERVICE_URL: str = "http://localhost:8007"
    LEGAL_SERVICE_URL: str = "http://localhost:8008"
    NEWS_SERVICE_URL: str = "http://localhost:8006"
    KNOWLEDGE_SERVICE_URL: str = "http://localhost:8081"

    SEARCH_CACHE_TTL: int = 60
    HOT_SEARCH_CACHE_TTL: int = 300
    SERVICE_TIMEOUT: float = 10.0

    CORS_ORIGINS: str = "*"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL environment variable must be set")
        return v

    class Config:
        env_file = ".env"


settings = Settings()
