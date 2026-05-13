"""知识库服务配置"""
import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    ENVIRONMENT: str = Field(default="development", description="运行环境: development/production")

    service_name: str = "knowledge-service"
    service_host: str = Field(default="0.0.0.0")
    service_port: int = Field(default=8081)
    debug: bool = True

    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/knowledge_service")

    vector_store_path: str = Field(
        default="./data/chroma_knowledge",
        description="向量数据存储路径"
    )

    embedding_model: str = Field(default="shibing624/text2vec-base-chinese")

    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="允许的CORS来源"
    )

    stats_categories: List[dict] = Field(default=[
        {"name": "劳动", "count": 0},
        {"name": "合同", "count": 0},
        {"name": "婚姻家庭", "count": 0},
        {"name": "侵权责任", "count": 0},
        {"name": "债权债务", "count": 0},
        {"name": "刑事", "count": 0},
        {"name": "社会保险", "count": 0},
        {"name": "民法", "count": 0},
    ])

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_allowed_origins(self) -> List[str]:
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
