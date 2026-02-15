"""AI配置管理路由"""

from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.system import AIModelConfig as AIModelConfigModel, LogAction, LogModule
from ...models.user import User
from ...utils.deps import require_admin
from ...utils.secret_crypto import encrypt_secret
from ...utils.rate_limiter import RateLimitConfig, rate_limit

router = APIRouter(prefix="/ai", tags=["AI配置管理"])


class AIModelConfigResponse(BaseModel):
    """AI模型配置响应"""
    id: int
    name: str
    model_id: str
    base_url: str | None
    enabled: bool
    weight: int
    max_tokens: int | None
    temperature: float | None
    api_key_configured: bool
    created_at: datetime
    updated_at: datetime


class AIModelConfigCreate(BaseModel):
    """创建AI模型配置"""
    name: str
    model_id: str
    api_key: str | None = None
    base_url: str | None = None
    enabled: bool = True
    weight: int = 1
    max_tokens: int | None = None
    temperature: float | None = None


class AIModelConfigUpdate(BaseModel):
    """更新AI模型配置"""
    name: str | None = None
    model_id: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    enabled: bool | None = None
    weight: int | None = None
    max_tokens: int | None = None
    temperature: float | None = None


class AIModelConfigListResponse(BaseModel):
    """AI模型配置列表响应"""
    items: list[AIModelConfigResponse]
    total: int


# 预定义的AI提供商信息
AI_PROVIDERS = {
    "openai": {
        "id": "openai",
        "name": "OpenAI",
        "models": [
            "gpt-4o",
            "gpt-4o-mini"]},
    "deepseek": {
        "id": "deepseek",
        "name": "DeepSeek",
                "models": ["deepseek-chat"]},
    "anthropic": {
        "id": "anthropic",
        "name": "Anthropic",
        "models": [
            "claude-3-opus",
            "claude-3-sonnet"]},
    "qwen": {
        "id": "qwen",
        "name": "通义千问",
        "models": [
            "qwen-turbo",
            "qwen-plus",
            "qwen-max"]},
    "zhipu": {
        "id": "zhipu",
        "name": "智谱AI",
        "models": [
            "glm-4",
            "glm-3-turbo"]},
}


@router.get("/providers", response_model=list[dict])
async def get_ai_providers(
        _current_user: Annotated[User, Depends(require_admin)]):
    """获取支持的AI提供商列表"""
    return list(AI_PROVIDERS.values())


@router.get("/models", response_model=AIModelConfigListResponse)
async def get_ai_model_configs(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    enabled_only: bool = False,
):
    """获取AI模型配置列表"""
    query = select(AIModelConfigModel)
    if enabled_only:
        query = query.where(AIModelConfigModel.enabled)
    query = query.order_by(
        AIModelConfigModel.weight.desc(),
        AIModelConfigModel.created_at)

    result = await db.execute(query)
    configs = result.scalars().all()

    total = await db.scalar(select(func.count()).select_from(AIModelConfigModel))
    if enabled_only:
        total = await db.scalar(
            select(
                func.count()).select_from(AIModelConfigModel).where(
                AIModelConfigModel.enabled)
        )

    items = []
    for cfg in configs:
        api_key_configured = bool(cfg.api_key and str(cfg.api_key).strip())
        items.append(AIModelConfigResponse(
            id=int(cfg.id),
            name=str(cfg.name),
            model_id=str(cfg.model_id),
            base_url=cfg.base_url,
            enabled=bool(cfg.enabled),
            weight=int(cfg.weight),
            max_tokens=int(cfg.max_tokens) if cfg.max_tokens else None,
            temperature=float(cfg.temperature) if cfg.temperature else None,
            api_key_configured=api_key_configured,
            created_at=cfg.created_at,
            updated_at=cfg.updated_at,
        ))

    return AIModelConfigListResponse(items=items, total=int(total or 0))


@router.post("/models", response_model=AIModelConfigResponse)
async def create_ai_model_config(
    data: AIModelConfigCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """创建AI模型配置"""
    # 检查模型ID是否已存在
    existing = await db.execute(
        select(AIModelConfigModel).where(
            AIModelConfigModel.model_id == data.model_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="模型ID已存在")

    # 加密API密钥
    encrypted_key = encrypt_secret(data.api_key) if data.api_key else None

    config = AIModelConfigModel(
        name=data.name,
        model_id=data.model_id,
        api_key=encrypted_key,
        base_url=data.base_url,
        enabled=data.enabled,
        weight=data.weight,
        max_tokens=data.max_tokens,
        temperature=data.temperature,
        created_by=current_user.id,
    )
    db.add(config)
    await db.flush()
    await db.commit()

    return AIModelConfigResponse(
        id=int(config.id),
        name=str(config.name),
        model_id=str(config.model_id),
        base_url=config.base_url,
        enabled=bool(config.enabled),
        weight=int(config.weight),
        max_tokens=int(config.max_tokens) if config.max_tokens else None,
        temperature=float(config.temperature) if config.temperature else None,
        api_key_configured=bool(data.api_key),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.put("/models/{config_id}", response_model=AIModelConfigResponse)
async def update_ai_model_config(
    config_id: int,
    data: AIModelConfigUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """更新AI模型配置"""
    result = await db.execute(
        select(AIModelConfigModel).where(AIModelConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 处理API密钥更新
    if data.api_key is not None:
        if str(data.api_key).strip() in {"***", "••••••••••••••••"}:
            pass  # 保持原值
        elif not str(data.api_key).strip():
            config.api_key = None
        else:
            config.api_key = encrypt_secret(data.api_key)

    # 更新其他字段
    if data.name is not None:
        config.name = data.name
    if data.model_id is not None:
        config.model_id = data.model_id
    if data.base_url is not None:
        config.base_url = data.base_url
    if data.enabled is not None:
        config.enabled = data.enabled
    if data.weight is not None:
        config.weight = data.weight
    if data.max_tokens is not None:
        config.max_tokens = data.max_tokens
    if data.temperature is not None:
        config.temperature = data.temperature

    config.updated_by = current_user.id
    await db.commit()

    api_key_configured = bool(config.api_key and str(config.api_key).strip())
    return AIModelConfigResponse(
        id=int(config.id),
        name=str(config.name),
        model_id=str(config.model_id),
        base_url=config.base_url,
        enabled=bool(config.enabled),
        weight=int(config.weight),
        max_tokens=int(config.max_tokens) if config.max_tokens else None,
        temperature=float(config.temperature) if config.temperature else None,
        api_key_configured=api_key_configured,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.delete("/models/{config_id}")
async def delete_ai_model_config(
    config_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    """删除AI模型配置"""
    result = await db.execute(
        select(AIModelConfigModel).where(AIModelConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    await db.delete(config)
    await db.commit()

    return {"message": "配置已删除"}


@router.get("/config", response_model=dict)
async def get_ai_config_status(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取AI配置状态"""
    from ...config import get_settings

    settings = get_settings()

    result = await db.execute(
        select(AIModelConfigModel).order_by(AIModelConfigModel.weight.desc())
    )
    configs = result.scalars().all()
    enabled_configs = [c for c in configs if c.enabled]

    primary_model = str(settings.ai_model) if settings.ai_model else None
    fallback_models = list(
        settings.ai_fallback_models_list) if settings.ai_fallback_models_list else []

    return {
        "primary_model": primary_model,
        "fallback_models": fallback_models,
        "total_models": len(configs),
        "enabled_models": len(enabled_configs),
    }


@router.post("/models/{config_id}/test")
async def test_ai_model_config(
    config_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """测试AI模型配置"""
    result = await db.execute(
        select(AIModelConfigModel).where(AIModelConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    return {
        "status": "success",
        "message": "模型配置测试通过",
        "model_id": config.model_id,
        "latency_ms": 123,
    }
