"""法律服务配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class LegalSettings(BaseSettings):
    """法律服务配置"""

    service_name: str = "legal-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8004

    database_url: str = os.getenv(
        "LEGAL_DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/legal_service"
    )
    db_pool_size: int = 20
    db_max_overflow: int = 30

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # AI服务配置
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o"

    # ChromaDB配置
    chroma_persist_dir: str = "./chroma_db"

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> LegalSettings:
    return LegalSettings()
