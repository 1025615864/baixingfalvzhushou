"""法律服务配置"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """法律服务配置"""

    service_name: str = "legal-service"
    service_host: str = "0.0.0.0"
    service_port: int = 8008
    grpc_port: int = int(os.getenv("GRPC_PORT", "50052"))

    database_url: str = os.getenv(
        "LEGAL_DATABASE_URL",
        "postgresql+asyncpg://user:pass@localhost:5432/legal_service"
    )
    db_pool_size: int = 20
    db_max_overflow: int = 30

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_enabled: bool = os.getenv("KAFKA_ENABLED", "false").lower() in {"1", "true", "yes"}
    kafka_consumer_group_id: str = "legal-service-user-events"

    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://localhost:8005")
    ai_service_enabled: bool = os.getenv("AI_SERVICE_ENABLED", "false").lower() in {"1", "true", "yes"}

    consul_enabled: bool = os.getenv("CONSUL_ENABLED", "false").lower() in {"1", "true", "yes"}

    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in {"1", "true", "yes"}

    otel_exporter_otlp_endpoint: Optional[str] = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    grpc_use_tls: bool = os.getenv("GRPC_USE_TLS", "false").lower() in {"1", "true", "yes"}

    env: str = os.getenv("ENV", "development")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()