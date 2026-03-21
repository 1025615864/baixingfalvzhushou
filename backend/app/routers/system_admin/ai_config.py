"""AI配置管理路由"""

import logging
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
from ...services.ai.config_manager import get_config_manager, RotationStrategy

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI配置管理"])


class AIModelConfigResponse(BaseModel):
    """AI模型配置响应"""
    id: int
    name: str
    provider: str
    model_id: str
    base_url: str | None
    enabled: bool
    weight: int
    priority: int
    is_primary: bool
    max_tokens: int | None
    temperature: float | None
    api_key_configured: bool
    call_count: int
    error_count: int
    last_used_at: datetime | None
    health_status: str
    last_health_check: datetime | None
    health_check_message: str | None
    created_at: datetime
    updated_at: datetime


class AIModelConfigCreate(BaseModel):
    """创建AI模型配置"""
    name: str
    provider: str = "openai"
    model_id: str
    api_key: str | None = None
    base_url: str | None = None
    enabled: bool = True
    weight: int = 1
    priority: int = 0
    is_primary: bool = False
    max_tokens: int | None = None
    temperature: float | None = None


class AIModelConfigUpdate(BaseModel):
    """更新AI模型配置"""
    name: str | None = None
    provider: str | None = None
    model_id: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    enabled: bool | None = None
    weight: int | None = None
    priority: int | None = None
    is_primary: bool | None = None
    max_tokens: int | None = None
    temperature: float | None = None


class AIModelConfigListResponse(BaseModel):
    """AI模型配置列表响应"""
    items: list[AIModelConfigResponse]
    total: int


class AIModelConfigStats(BaseModel):
    """AI模型配置统计"""
    total: int
    enabled: int
    healthy: int
    degraded: int
    unhealthy: int
    unknown: int
    total_calls: int
    total_errors: int


class BatchOperationRequest(BaseModel):
    """批量操作请求"""
    ids: list[int]
    action: str  # enable, disable, delete


class BatchOperationResponse(BaseModel):
    """批量操作响应"""
    success: int
    failed: int
    message: str


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
    provider: str | None = None,
):
    """获取AI模型配置列表"""
    query = select(AIModelConfigModel)
    if enabled_only:
        query = query.where(AIModelConfigModel.enabled)
    if provider:
        query = query.where(AIModelConfigModel.provider == provider)
    query = query.order_by(
        AIModelConfigModel.priority.desc(),
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
            provider=str(cfg.provider),
            model_id=str(cfg.model_id),
            base_url=cfg.base_url,
            enabled=bool(cfg.enabled),
            weight=int(cfg.weight),
            priority=int(cfg.priority),
            is_primary=bool(cfg.is_primary),
            max_tokens=int(cfg.max_tokens) if cfg.max_tokens else None,
            temperature=float(cfg.temperature) if cfg.temperature else None,
            api_key_configured=api_key_configured,
            call_count=int(cfg.call_count),
            error_count=int(cfg.error_count),
            last_used_at=cfg.last_used_at,
            health_status=str(cfg.health_status),
            last_health_check=cfg.last_health_check,
            health_check_message=cfg.health_check_message,
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
        provider=data.provider,
        model_id=data.model_id,
        api_key=encrypted_key,
        base_url=data.base_url,
        enabled=data.enabled,
        weight=data.weight,
        priority=data.priority,
        is_primary=data.is_primary,
        max_tokens=data.max_tokens,
        temperature=data.temperature,
        created_by=current_user.id,
    )
    db.add(config)
    await db.flush()
    await db.commit()

    # 清除配置管理器缓存
    get_config_manager().clear_cache()

    return AIModelConfigResponse(
        id=int(config.id),
        name=str(config.name),
        provider=str(config.provider),
        model_id=str(config.model_id),
        base_url=config.base_url,
        enabled=bool(config.enabled),
        weight=int(config.weight),
        priority=int(config.priority),
        is_primary=bool(config.is_primary),
        max_tokens=int(config.max_tokens) if config.max_tokens else None,
        temperature=float(config.temperature) if config.temperature else None,
        api_key_configured=bool(data.api_key),
        call_count=0,
        error_count=0,
        last_used_at=None,
        health_status="unknown",
        last_health_check=None,
        health_check_message=None,
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
    if data.provider is not None:
        config.provider = data.provider
    if data.model_id is not None:
        config.model_id = data.model_id
    if data.base_url is not None:
        config.base_url = data.base_url
    if data.enabled is not None:
        config.enabled = data.enabled
    if data.weight is not None:
        config.weight = data.weight
    if data.priority is not None:
        config.priority = data.priority
    if data.is_primary is not None:
        config.is_primary = data.is_primary
    if data.max_tokens is not None:
        config.max_tokens = data.max_tokens
    if data.temperature is not None:
        config.temperature = data.temperature

    config.updated_by = current_user.id
    await db.commit()

    # 清除配置管理器缓存
    get_config_manager().clear_cache()

    api_key_configured = bool(config.api_key and str(config.api_key).strip())
    return AIModelConfigResponse(
        id=int(config.id),
        name=str(config.name),
        provider=str(config.provider),
        model_id=str(config.model_id),
        base_url=config.base_url,
        enabled=bool(config.enabled),
        weight=int(config.weight),
        priority=int(config.priority),
        is_primary=bool(config.is_primary),
        max_tokens=int(config.max_tokens) if config.max_tokens else None,
        temperature=float(config.temperature) if config.temperature else None,
        api_key_configured=api_key_configured,
        call_count=int(config.call_count),
        error_count=int(config.error_count),
        last_used_at=config.last_used_at,
        health_status=str(config.health_status),
        last_health_check=config.last_health_check,
        health_check_message=config.health_check_message,
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

    # 清除配置管理器缓存
    get_config_manager().clear_cache()

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

    # 执行实际的健康检查
    from ...services.ai.config_manager import AIConfig
    ai_config = AIConfig.from_model(config)
    config_manager = get_config_manager()

    import time
    start_time = time.time()
    is_healthy = await config_manager.perform_health_check(ai_config, db)
    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "status": "success" if is_healthy else "failed",
        "message": "模型配置测试通过" if is_healthy else "模型配置测试失败",
        "model_id": config.model_id,
        "provider": config.provider,
        "latency_ms": latency_ms,
        "health_status": config.health_status,
    }


@router.post("/models/batch", response_model=BatchOperationResponse)
async def batch_operation_ai_model_configs(
    data: BatchOperationRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """批量操作AI模型配置"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="未指定配置ID")

    if data.action not in ("enable", "disable", "delete"):
        raise HTTPException(status_code=400, detail="不支持的操作类型")

    success_count = 0
    failed_count = 0
    errors: list[str] = []

    for config_id in data.ids:
        try:
            result = await db.execute(
                select(AIModelConfigModel).where(AIModelConfigModel.id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                failed_count += 1
                errors.append(f"配置ID {config_id}: 不存在")
                logger.warning("批量操作失败 - 配置不存在: id=%d, action=%s", config_id, data.action)
                continue

            if data.action == "enable":
                config.enabled = True
            elif data.action == "disable":
                config.enabled = False
            elif data.action == "delete":
                await db.delete(config)

            success_count += 1
            logger.info(
                "批量操作成功: id=%d, action=%s, user=%d",
                config_id, data.action, current_user.id
            )
        except Exception as e:
            failed_count += 1
            error_msg = str(e)[:100]
            errors.append(f"配置ID {config_id}: {error_msg}")
            logger.error(
                "批量操作异常: id=%d, action=%s, error=%s",
                config_id, data.action, error_msg
            )

    await db.commit()

    # 清除配置管理器缓存
    get_config_manager().clear_cache()

    # 构建消息
    action_text = {"enable": "启用", "disable": "禁用", "delete": "删除"}.get(data.action, data.action)
    message = f"成功{action_text} {success_count} 个配置"
    if failed_count > 0:
        message += f"，失败 {failed_count} 个"
    if errors:
        logger.warning("批量操作错误汇总: %s", "; ".join(errors[:5]))  # 只记录前5个错误

    return BatchOperationResponse(
        success=success_count,
        failed=failed_count,
        message=message,
    )


@router.get("/models/{config_id}/stats", response_model=dict)
async def get_ai_model_config_stats(
    config_id: int,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取单个AI模型配置的统计信息"""
    result = await db.execute(
        select(AIModelConfigModel).where(AIModelConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    return {
        "id": int(config.id),
        "name": str(config.name),
        "provider": str(config.provider),
        "model_id": str(config.model_id),
        "call_count": int(config.call_count),
        "error_count": int(config.error_count),
        "error_rate": round(config.error_count / max(config.call_count, 1) * 100, 2) if config.call_count > 0 else 0,
        "last_used_at": config.last_used_at,
        "health_status": str(config.health_status),
        "last_health_check": config.last_health_check,
        "health_check_message": config.health_check_message,
    }


@router.post("/models/{config_id}/health-check")
async def trigger_health_check(
    config_id: int,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """手动触发健康检查"""
    result = await db.execute(
        select(AIModelConfigModel).where(AIModelConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    from ...services.ai.config_manager import AIConfig
    ai_config = AIConfig.from_model(config)
    config_manager = get_config_manager()

    import time
    start_time = time.time()
    is_healthy = await config_manager.perform_health_check(ai_config, db)
    latency_ms = int((time.time() - start_time) * 1000)

    # 重新获取更新后的配置
    await db.refresh(config)

    return {
        "success": is_healthy,
        "health_status": config.health_status,
        "health_check_message": config.health_check_message,
        "latency_ms": latency_ms,
        "checked_at": config.last_health_check,
    }


@router.get("/stats/summary", response_model=AIModelConfigStats)
async def get_ai_config_stats_summary(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: str | None = None,
):
    """获取AI配置统计概览"""
    config_manager = get_config_manager()
    stats = await config_manager.get_stats(db, provider=provider)
    return AIModelConfigStats(**stats)
