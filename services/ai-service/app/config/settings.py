"""AI服务配置"""
import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """AI服务配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    ENVIRONMENT: str = Field(default="development", description="运行环境: development/production")

    database_url: str = Field(
        default="postgresql+asyncpg://ai_user:password@localhost:5432/ai_service",
        description="AI服务数据库连接"
    )
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=100)
    db_pool_recycle: int = Field(default=3600, ge=300)

    openai_api_key: str = Field(
        default="",
        description="DeepSeek API Key (必填)"
    )
    openai_base_url: str = Field(default="https://api.deepseek.com/v1")
    llm_model: str = Field(default="deepseek-chat")

    secondary_llm_url: Optional[str] = Field(default=None)
    secondary_llm_key: Optional[str] = Field(default=None)
    secondary_llm_model: str = Field(default="deepseek-reasoner")

    circuit_breaker_threshold: int = Field(default=5, ge=1)
    circuit_breaker_timeout: int = Field(default=30, ge=5)

    max_tokens: int = Field(default=2000, ge=100, le=8000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

    user_service_url: str = Field(default="http://localhost:8001")
    backend_url: str = Field(default="http://localhost:8000")
    legal_service_url: str = Field(default="http://localhost:8008")
    use_remote_session: bool = Field(default=True)

    knowledge_service_url: str = Field(default="http://localhost:8081")
    archive_service_url: str = Field(default="http://localhost:8082")
    embedding_service_url: str = Field(default="http://localhost:8006")

    internal_api_key: str = Field(default="internal-api-key-change-in-production")

    rag_level1_timeout_ms: int = Field(default=500, ge=100)
    rag_level2_timeout_ms: int = Field(default=2000, ge=500)
    rag_min_similarity: float = Field(default=0.75, ge=0.0, le=1.0)

    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="允许的CORS来源"
    )

    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or len(v) < 10:
            raise ValueError("OPENAI_API_KEY is required and must be a valid API key")
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_allowed_origins(self) -> list[str]:
        if self.is_production:
            return [
                "https://www.baixingfalv.com",
                "https://app.baixingfalv.com",
                "https://admin.baixingfalv.com",
            ]
        return self.cors_origins

    def get_cors_config(self) -> dict:
        return {
            "allow_origins": self.cors_allowed_origins,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
