from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    SERVICE_NAME: str = "embedding-service"
    SERVICE_PORT: int = 8003
    ENVIRONMENT: str = "development"

    EMBEDDING_MODEL: str = "shibing624/text2vec-base-chinese"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_DIM: int = 768
    DEFAULT_BATCH_SIZE: int = 32
    MAX_BATCH_SIZE: int = 512
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 100

    cors_allowed_origins: List[str] = ["*"]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    def get_cors_config(self) -> dict:
        return {
            "allow_origins": self.cors_allowed_origins,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }


_settings: Settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
