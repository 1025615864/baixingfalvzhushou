"""AI服务配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class AISettings(BaseSettings):
    """AI服务配置"""

    service_name: str = "ai-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8005

    database_url: str = os.getenv(
        "AI_DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/ai_service"
    )
    db_pool_size: int = 20
    db_max_overflow: int = 30

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # OpenAI配置
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    openai_fallback_models: str = os.getenv("OPENAI_FALLBACK_MODELS", "gpt-4o-mini,deepseek-chat")

    # DeepSeek配置（备选）
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # ChromaDB配置
    chroma_persist_dir: str = "./chroma_db"

    # 法律助手Agent配置
    agent_config_version: str = "v1"
    agent_prompt_version: str = "v1"

    # RAG配置
    rag_top_k: int = 5
    rag_score_threshold: float = 0.7

    # 熔断器配置
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 30

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> AISettings:
    return AISettings()
