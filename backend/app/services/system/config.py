"""系统配置和密钥管理服务"""
from typing import Annotated
from datetime import datetime, timezone
from fastapi import Depends, HTTPException
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.system import SystemConfig, SystemSecret


def _mask_secret_value(value: str | None) -> str | None:
    """脱敏密钥值"""
    if value is None:
        return None
    if not str(value).strip():
        return None
    return "***"


class SystemConfigService:
    @staticmethod
    def is_secret_key(key: str) -> bool:
        """Check if a config key contains sensitive information"""
        secret_keywords = [
            'password', 'secret', 'token', 'key', 'api_key', 'apikey',
            'access_token', 'auth_token', 'bearer', 'credential'
        ]
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in secret_keywords)
    """系统配置服务"""

    @staticmethod
    async def get_config(
        db: Annotated[AsyncSession, Depends(get_db)],
        key: str,
    ) -> SystemConfig | None:
        """获取配置"""
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_configs(
        db: Annotated[AsyncSession, Depends(get_db)],
        category: str | None = None,
    ) -> list[SystemConfig]:
        """获取所有配置"""
        query = select(SystemConfig)
        if category:
            query = query.where(SystemConfig.category == category)
        query = query.order_by(SystemConfig.category, SystemConfig.key)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def set_config(
        db: Annotated[AsyncSession, Depends(get_db)],
        key: str,
        value: str | None,
        description: str | None = None,
        category: str = "general",
        updated_by: int | None = None,
    ) -> SystemConfig:
        """设置配置"""
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()

        if config:
            config.value = value
            config.updated_at = datetime.now(timezone.utc)
            if updated_by:
                config.updated_by = updated_by
        else:
            config = SystemConfig(
                key=key,
                value=value,
                description=description,
                category=category,
                created_by=updated_by,
                updated_by=updated_by,
            )
            db.add(config)

        await db.commit()
        await db.refresh(config)
        return config

    @staticmethod
    async def delete_config(
        db: Annotated[AsyncSession, Depends(get_db)],
        key: str,
    ) -> bool:
        """删除配置"""
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        config = result.scalar_one_or_none()

        if not config:
            return False

        await db.delete(config)
        await db.commit()
        return True

    @staticmethod
    async def batch_update(
        db: Annotated[AsyncSession, Depends(get_db)],
        configs: list[dict],
        updated_by: int | None = None,
    ) -> list[SystemConfig]:
        """批量更新配置"""
        results = []
        for item in configs:
            config = await SystemConfigService.set_config(
                db=db,
                key=item["key"],
                value=item.get("value"),
                description=item.get("description"),
                category=item.get("category", "general"),
                updated_by=updated_by,
            )
            results.append(config)
        return results


class SystemSecretService:
    """系统密钥服务（敏感配置）"""

    @staticmethod
    async def get_all(
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> list[SystemSecret]:
        """获取所有密钥"""
        query = select(SystemSecret).order_by(SystemSecret.key)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get(
        db: Annotated[AsyncSession, Depends(get_db)],
        key: str,
    ) -> SystemSecret | None:
        """获取密钥"""
        result = await db.execute(
            select(SystemSecret).where(SystemSecret.key == key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def set(
        db: Annotated[AsyncSession, Depends(get_db)],
        key: str,
        value: str | None,
        description: str | None = None,
        updated_by: int | None = None,
    ) -> SystemSecret:
        """设置密钥"""
        result = await db.execute(
            select(SystemSecret).where(SystemSecret.key == key)
        )
        secret = result.scalar_one_or_none()

        if secret:
            secret.value = value
            secret.updated_at = datetime.now(timezone.utc)
            if updated_by:
                secret.updated_by = updated_by
        else:
            secret = SystemSecret(
                key=key,
                value=value,
                description=description,
                created_by=updated_by,
                updated_by=updated_by,
            )
            db.add(secret)

        await db.commit()
        await db.refresh(secret)
        return secret

    @staticmethod
    async def delete(
        db: Annotated[AsyncSession, Depends(get_db)],
        key: str,
    ) -> bool:
        """删除密钥"""
        result = await db.execute(
            select(SystemSecret).where(SystemSecret.key == key)
        )
        secret = result.scalar_one_or_none()

        if not secret:
            return False

        await db.delete(secret)
        await db.commit()
        return True

    @staticmethod
    async def exists(
        db: Annotated[AsyncSession, Depends(get_db)],
        key: str,
    ) -> bool:
        """检查密钥是否存在"""
        result = await db.execute(
            select(SystemSecret.key).where(SystemSecret.key == key)
        )
        return result.scalar_one_or_none() is not None
