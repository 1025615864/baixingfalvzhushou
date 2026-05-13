"""System configuration service."""
from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass, field


_SECRET_KEYWORDS = ("password", "secret", "token", "key", "private", "credential")


def _mask_secret_value(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    if not value.strip():
        return None
    return "***"


class SystemConfigService:
    @staticmethod
    def is_secret_key(key: str) -> bool:
        lower = key.lower()
        return any(kw in lower for kw in _SECRET_KEYWORDS)

    @classmethod
    async def get_config(cls, db: Any, key: str) -> Any:
        from sqlalchemy import select
        from app.models.system import SystemConfig
        result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
        return result.scalar_one_or_none()

    @classmethod
    async def get_all_configs(cls, db: Any, category: Optional[str] = None) -> list:
        from sqlalchemy import select
        from app.models.system import SystemConfig
        stmt = select(SystemConfig)
        if category:
            stmt = stmt.where(SystemConfig.category == category)
        result = await db.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def set_config(
        cls,
        db: Any,
        key: str,
        value: str,
        description: str = "",
        category: str = "general",
        updated_by: int = 0,
    ) -> Any:
        from app.models.system import SystemConfig
        existing = await cls.get_config(db, key)
        if existing:
            existing.value = value
            if description:
                existing.description = description
            if category:
                existing.category = category
            existing.updated_by = updated_by
            await db.commit()
            await db.refresh(existing)
            return existing
        config = SystemConfig(
            key=key,
            value=value,
            description=description,
            category=category,
            updated_by=updated_by,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    @classmethod
    async def delete_config(cls, db: Any, key: str) -> bool:
        config = await cls.get_config(db, key)
        if config is None:
            return False
        await db.delete(config)
        await db.commit()
        return True

    @classmethod
    async def batch_update(cls, db: Any, configs: list[dict], updated_by: int = 0) -> list:
        results = []
        for item in configs:
            config = await cls.set_config(
                db,
                key=item["key"],
                value=item["value"],
                updated_by=updated_by,
            )
            results.append(config)
        return results


class SystemSecretService:
    @classmethod
    async def get_all(cls, db: Any) -> list:
        from sqlalchemy import select
        from app.models.system import SystemSecret
        result = await db.execute(select(SystemSecret))
        return result.scalars().all()

    @classmethod
    async def get(cls, db: Any, key: str) -> Any:
        from sqlalchemy import select
        from app.models.system import SystemSecret
        result = await db.execute(select(SystemSecret).where(SystemSecret.key == key))
        return result.scalar_one_or_none()

    @classmethod
    async def set(
        cls,
        db: Any,
        key: str,
        value: str,
        description: str = "",
        updated_by: int = 0,
    ) -> Any:
        from app.models.system import SystemSecret
        existing = await cls.get(db, key)
        if existing:
            existing.encrypted_value = value
            if description:
                existing.description = description
            existing.updated_by = updated_by
            await db.commit()
            await db.refresh(existing)
            return existing
        secret = SystemSecret(
            key=key,
            encrypted_value=value,
            description=description,
            updated_by=updated_by,
        )
        db.add(secret)
        await db.commit()
        await db.refresh(secret)
        return secret

    @classmethod
    async def delete(cls, db: Any, key: str) -> bool:
        secret = await cls.get(db, key)
        if secret is None:
            return False
        await db.delete(secret)
        await db.commit()
        return True

    @classmethod
    async def exists(cls, db: Any, key: str) -> bool:
        from sqlalchemy import select
        from app.models.system import SystemSecret
        result = await db.execute(
            select(SystemSecret.key).where(SystemSecret.key == key)
        )
        return result.scalar_one_or_none() is not None


system_config_service = SystemConfigService()
