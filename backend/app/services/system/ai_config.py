"""AI模型配置服务"""
from fastapi import HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import AIModelConfig as AIModelConfigModel
from app.utils.secret_crypto import encrypt_secret


class AIModelConfigService:
    """AI模型配置服务"""

    @staticmethod
    async def get_list(
        db: AsyncSession,
        enabled_only: bool = False,
    ) -> tuple[list[AIModelConfigModel], int]:
        """获取AI模型配置列表"""
        query = select(AIModelConfigModel)
        if enabled_only:
            query = query.where(AIModelConfigModel.enabled)
        query = query.order_by(
            AIModelConfigModel.weight.desc(),
            AIModelConfigModel.created_at)

        result = await db.execute(query)
        configs = result.scalars().all()

        total_query = select(func.count()).select_from(AIModelConfigModel)
        if enabled_only:
            total_query = total_query.where(AIModelConfigModel.enabled)
        total = await db.scalar(total_query)

        return list(configs), int(total or 0)

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        config_id: int,
    ) -> AIModelConfigModel | None:
        """根据ID获取AI模型配置"""
        result = await db.execute(
            select(AIModelConfigModel).where(
                AIModelConfigModel.id == config_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        model_id: str,
        api_key: str | None,
        base_url: str | None,
        enabled: bool,
        weight: int,
        max_tokens: int | None,
        temperature: float | None,
        created_by: int,
    ) -> AIModelConfigModel:
        """创建AI模型配置"""
        # 检查模型ID是否已存在
        existing = await db.execute(
            select(AIModelConfigModel).where(
                AIModelConfigModel.model_id == model_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="模型ID已存在")

        # 加密API密钥
        encrypted_key = encrypt_secret(api_key) if api_key else None

        config = AIModelConfigModel(
            name=name,
            model_id=model_id,
            api_key=encrypted_key,
            base_url=base_url,
            enabled=enabled,
            weight=weight,
            max_tokens=max_tokens,
            temperature=temperature,
            created_by=created_by,
        )
        db.add(config)
        await db.flush()
        await db.commit()
        await db.refresh(config)

        return config

    @staticmethod
    async def update(
        db: AsyncSession,
        config_id: int,
        name: str | None = None,
        model_id: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        enabled: bool | None = None,
        weight: int | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        updated_by: int | None = None,
    ) -> AIModelConfigModel:
        """更新AI模型配置"""
        result = await db.execute(
            select(AIModelConfigModel).where(
                AIModelConfigModel.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        # 处理API密钥更新
        if api_key is not None:
            if str(api_key).strip() in {"***", "••••••••••••••••"}:
                pass  # 保持原值
            elif not str(api_key).strip():
                config.api_key = None
            else:
                config.api_key = encrypt_secret(api_key)

        # 更新其他字段
        if name is not None:
            config.name = name
        if model_id is not None:
            # 检查新模型ID是否与其他配置冲突
            existing = await db.execute(
                select(AIModelConfigModel).where(
                    and_(
                        AIModelConfigModel.model_id == model_id,
                        AIModelConfigModel.id != config_id)
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="模型ID已被其他配置使用")
            config.model_id = model_id
        if base_url is not None:
            config.base_url = base_url
        if enabled is not None:
            config.enabled = enabled
        if weight is not None:
            config.weight = weight
        if max_tokens is not None:
            config.max_tokens = max_tokens
        if temperature is not None:
            config.temperature = temperature
        if updated_by is not None:
            config.updated_by = updated_by

        await db.commit()
        await db.refresh(config)

        return config

    @staticmethod
    async def delete(
        db: AsyncSession,
        config_id: int,
    ) -> bool:
        """删除AI模型配置"""
        result = await db.execute(
            select(AIModelConfigModel).where(
                AIModelConfigModel.id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="配置不存在")

        await db.delete(config)
        await db.commit()

        return True
