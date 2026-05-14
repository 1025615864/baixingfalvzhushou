"""新闻服务配置"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "news-service"
    service_port: int = 8006
    service_host: str = "0.0.0.0"
    debug: bool = True

    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/news")
    db_pool_size: int = 20
    db_max_overflow: int = 30

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://localhost:8004")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    news_llm_model: str = os.getenv("NEWS_LLM_MODEL", "deepseek-chat")
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "internal-api-key-change-in-production")

    class Config:
        env_file = ".env"
        extra = "ignore"

    def get_cors_config(self):
        return {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }


_settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
