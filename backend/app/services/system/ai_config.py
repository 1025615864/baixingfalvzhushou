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

    @classmethod
    async def get_list(cls, db, enabled_only: bool = False) -> tuple[list, int]:
        from sqlalchemy import select, func
        from app.models.system import AIModelConfig as AIModelConfigModel
        count_stmt = select(func.count()).select_from(AIModelConfigModel)
        result = await db.execute(count_stmt)
        total = result.scalar() or 0
        stmt = select(AIModelConfigModel)
        if enabled_only:
            stmt = stmt.where(AIModelConfigModel.enabled.is_(True))
        result = await db.execute(stmt)
        configs = result.scalars().all()
        return configs, total

    @classmethod
    async def get_by_id(cls, db, config_id: int):
        from sqlalchemy import select
        from app.models.system import AIModelConfig as AIModelConfigModel
        stmt = select(AIModelConfigModel).where(AIModelConfigModel.id == config_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        from sqlalchemy import select
        from app.models.system import AIModelConfig as AIModelConfigModel
        model_id = kwargs.get("model_id")
        if model_id:
            dup_stmt = select(AIModelConfigModel).where(AIModelConfigModel.model_id == model_id)
            dup_result = await db.execute(dup_stmt)
            if dup_result.scalar_one_or_none() is not None:
                raise ValueError("模型ID已存在")
        api_key = kwargs.pop("api_key", None)
        if api_key:
            try:
                from app.services.crypto import encrypt_secret
                kwargs["api_key"] = encrypt_secret(api_key)
            except Exception:
                try:
                    from app.services.settlement.crypto import encrypt_secret
                    kwargs["api_key"] = encrypt_secret(api_key)
                except Exception:
                    kwargs["api_key"] = api_key
        config = AIModelConfigModel(**kwargs)
        db.add(config)
        await db.flush()
        await db.refresh(config)
        return config

    @classmethod
    async def update(cls, db, config_id: int, **kwargs):
        config = await cls.get_by_id(db, config_id)
        if config is None:
            raise ValueError("配置不存在")
        model_id = kwargs.get("model_id")
        if model_id:
            from sqlalchemy import select
            from app.models.system import AIModelConfig as AIModelConfigModel
            dup_stmt = select(AIModelConfigModel).where(
                AIModelConfigModel.model_id == model_id,
                AIModelConfigModel.id != config_id,
            )
            dup_result = await db.execute(dup_stmt)
            if dup_result.scalar_one_or_none() is not None:
                raise ValueError("模型ID已被其他配置使用")
        api_key = kwargs.pop("api_key", None)
        if api_key is not None:
            if api_key == "***":
                pass
            elif api_key == "":
                kwargs["api_key"] = ""
            else:
                try:
                    from app.services.crypto import encrypt_secret
                    kwargs["api_key"] = encrypt_secret(api_key)
                except Exception:
                    try:
                        from app.services.settlement.crypto import encrypt_secret
                        kwargs["api_key"] = encrypt_secret(api_key)
                    except Exception:
                        kwargs["api_key"] = api_key
        for k, v in kwargs.items():
            if v is not None and hasattr(config, k):
                setattr(config, k, v)
        await db.flush()
        await db.refresh(config)
        return config

    @classmethod
    async def delete(cls, db, config_id: int) -> bool:
        config = await cls.get_by_id(db, config_id)
        if config is None:
            raise ValueError("配置不存在")
        await db.delete(config)
        await db.flush()
        return True


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
