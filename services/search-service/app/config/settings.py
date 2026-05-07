"""搜索服务配置"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "search-service"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/search_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
