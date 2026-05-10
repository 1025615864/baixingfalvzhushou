"""AI configuration service."""
from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class AIModelConfig:
    model_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    enabled: bool = True


class AIModelConfigService:
    def __init__(self):
        self._models: dict[str, AIModelConfig] = {}

    def register_model(self, model_id: str, **kwargs) -> AIModelConfig:
        config = AIModelConfig(model_id=model_id, **kwargs)
        self._models[model_id] = config
        return config

    def get_model_config(self, model_id: str) -> Optional[AIModelConfig]:
        return self._models.get(model_id)

    def list_models(self) -> list[AIModelConfig]:
        return list(self._models.values())

    def get_enabled_models(self) -> list[AIModelConfig]:
        return [m for m in self._models.values() if m.enabled]

    def update_model(self, model_id: str, **kwargs) -> Optional[AIModelConfig]:
        config = self._models.get(model_id)
        if config is None:
            return None
        for k, v in kwargs.items():
            if hasattr(config, k):
                setattr(config, k, v)
        return config

    def delete_model(self, model_id: str) -> bool:
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False


class AIConfigService:
    def __init__(self):
        self._model_config_service = AIModelConfigService()

    def register_model(self, model_id: str, **kwargs) -> AIModelConfig:
        return self._model_config_service.register_model(model_id, **kwargs)

    def get_model_config(self, model_id: str) -> Optional[AIModelConfig]:
        return self._model_config_service.get_model_config(model_id)

    def list_models(self) -> list[AIModelConfig]:
        return self._model_config_service.list_models()


ai_config_service = AIConfigService()
