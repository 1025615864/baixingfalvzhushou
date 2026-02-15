"""系统配置路由"""

import json
import base64
import binascii
import re
import logging

from datetime import datetime
from typing import Annotated, cast
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.system import SystemConfig
from ...models.user import User
from ...utils.deps import require_admin
from ...services.system.config_gateway import config_gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/configs", tags=["系统配置"])


def _news_ai_providers_config_contains_api_key(decoded_json: str) -> bool:
    s = str(decoded_json or "").strip()
    if not s:
        return False
    try:
        obj_raw: object = cast(object, json.loads(s))
        if isinstance(obj_raw, list):
            for item_obj in cast(list[object], obj_raw):
                if not isinstance(item_obj, dict):
                    continue
                item_dict = cast(dict[object, object], item_obj)
                for k_obj in item_dict.keys():
                    kk = str(k_obj or "").strip().lower()
                    if kk in {"api_key", "apikey"}:
                        return True
            return False
        if isinstance(obj_raw, dict):
            obj_dict = cast(dict[object, object], obj_raw)
            for k_obj in obj_dict.keys():
                kk = str(k_obj or "").strip().lower()
                if kk in {"api_key", "apikey"}:
                    return True
            return False
    except Exception:
        logger.exception("Failed to parse JSON for API key check")
        return bool(
            re.search(
                r'"api_key"|\bapi_key\b|"apikey"|\bapikey\b',
                s,
                flags=re.IGNORECASE))
    return False


def _validate_system_config_no_secrets(key: str, value: str | None) -> None:
    k = str(key or "").strip()
    if value is None or not str(value).strip():
        return

    k_upper = k.upper()
    k_lower = k.lower()
    providers_prefixes = (
        "NEWS_AI_SUMMARY_LLM_PROVIDERS_JSON",
        "NEWS_AI_SUMMARY_LLM_PROVIDERS_B64")
    is_providers_key = k_upper in providers_prefixes or any(
        k_upper.startswith(f"{p}_") for p in providers_prefixes)
    if (
        any(token in k_lower for token in (
            "secret", "password", "api_key", "apikey", "private_key"))
        and not is_providers_key
    ):
        raise HTTPException(
            status_code=400,
            detail="Secret values must not be stored in SystemConfig. Use environment variables / Secret Manager.",
        )

    if not is_providers_key:
        return

    decoded = str(value)
    if k_upper.startswith("NEWS_AI_SUMMARY_LLM_PROVIDERS_B64"):
        try:
            decoded = base64.b64decode(str(value).strip()).decode("utf-8")
        except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
            raise HTTPException(
                status_code=400,
                detail="Providers config must be valid base64",
            ) from exc

    if _news_ai_providers_config_contains_api_key(decoded):
        raise HTTPException(
            status_code=400,
            detail="Providers config must not include api_key",
        )


class ConfigItemResponse(BaseModel):
    """配置项响应"""
    id: str
    key: str
    value: str | None
    default_value: str | None
    description: str | None
    type: str
    options: list[str] | None
    group: str
    is_editable: bool
    is_sensitive: bool
    updated_at: datetime | None
    updated_by: str | None


class ConfigGroupResponse(BaseModel):
    """配置分组响应"""
    id: str
    name: str
    description: str
    icon: str | None
    order: int
    config_count: int


class ConfigListResponse(BaseModel):
    """配置列表响应"""
    configs: list[ConfigItemResponse]
    groups: list[ConfigGroupResponse]


def _infer_config_type(value: str | None) -> str:
    """推断配置类型"""
    if value is None:
        return "string"
    value_lower = value.lower().strip()
    if value_lower in ("true", "false", "1", "0", "yes", "no"):
        return "boolean"
    try:
        float(value)
        return "number"
    except ValueError:
        pass
    if value.startswith("[") and value.endswith("]"):
        return "array"
    if value.startswith("{") and value.endswith("}"):
        return "json"
    return "string"


def _get_config_options(key: str) -> list[str] | None:
    """获取配置选项（用于select类型）"""
    # 可以在这里定义一些预定义的选项
    options_map = {
        "theme": ["light", "dark", "auto"],
        "language": ["zh-CN", "en-US"],
    }
    return options_map.get(key)


@router.get("", response_model=ConfigListResponse)
async def get_all_configs(
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    group: str | None = None,
):
    """获取所有系统配置"""
    # 获取配置列表
    query = select(SystemConfig)
    if group:
        query = query.where(SystemConfig.category == group)
    query = query.order_by(SystemConfig.category, SystemConfig.key)

    result = await db.execute(query)
    configs = result.scalars().all()

    # 构建配置项响应
    config_items = []
    for c in configs:
        config_type = _infer_config_type(c.value)
        config_items.append(ConfigItemResponse(
            id=c.key,  # 使用 key 作为 id
            key=c.key,
            value=c.value,
            default_value=c.value,  # 暂时用当前值作为默认值
            description=c.description or "",
            type=config_type,
            options=_get_config_options(c.key),
            group=c.category,
            is_editable=True,  # 默认可编辑
            is_sensitive=_is_sensitive_key(c.key),
            updated_at=c.updated_at,
            updated_by=None,  # 后端暂未记录更新者
        ))

    # 构建分组响应
    # 获取所有唯一的 category
    categories = set(c.category for c in configs)
    groups = []
    for idx, cat in enumerate(sorted(categories)):
        cat_configs = [c for c in configs if c.category == cat]
        groups.append(ConfigGroupResponse(
            id=cat,
            name=cat.capitalize(),
            description=f"{cat} related configurations",
            icon=None,
            order=idx,
            config_count=len(cat_configs),
        ))

    return ConfigListResponse(
        configs=config_items,
        groups=groups,
    )


def _is_sensitive_key(key: str) -> bool:
    """检查是否为敏感配置项"""
    sensitive_keywords = ["password", "secret", "key", "token", "api_key", "private"]
    key_lower = key.lower()
    return any(kw in key_lower for kw in sensitive_keywords)


@router.get("/{key}")
async def get_config(
    key: str,
    _current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取单个配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return {"key": key, "value": config.value}


@router.put("/{key}")
async def update_config(
    key: str,
    config_data: dict,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """更新配置"""
    value = config_data.get("value")
    description = config_data.get("description")
    category = config_data.get("category", "general")

    secret_keys = {
        "openai_api_key",
        "jwt_secret_key",
        "secret_key",
        "payment_webhook_secret",
        "redis_password",
        "database_password",
        "email_password",
        "smtp_password",
    }
    if str(key or "").strip().lower() in secret_keys:
        raise HTTPException(
            status_code=422,
            detail="Secret values must not be stored in SystemConfig. Use environment variables / Secret Manager.",
        )

    _validate_system_config_no_secrets(key, value)
    try:
        config_gateway.validate_value(key, value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()

    normalized_category = config_gateway.normalize_category(key, category)
    if config:
        config.value = value
        if description:
            config.description = description
        config.category = normalized_category or category
    else:
        config = SystemConfig(
            key=key,
            value=value,
            description=description,
            category=normalized_category or category,
        )
        db.add(config)

    await db.commit()
    return {"message": "配置已更新", "key": key}


@router.delete("/{key}")
async def delete_config(
    key: str,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """删除配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalar_one_or_none()

    if config:
        await db.delete(config)
        await db.commit()
        return {"message": "配置已删除"}
    raise HTTPException(status_code=404, detail="配置不存在")


class ConfigBatchItem(BaseModel):
    """批量配置项"""
    key: str
    value: str | None
    category: str = "general"
    description: str | None = None


class ConfigBatchRequest(BaseModel):
    """批量配置请求"""
    items: list[ConfigBatchItem]


@router.post("/batch")
async def batch_update_configs(
    request: ConfigBatchRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """批量更新配置"""
    for item in request.items:
        _validate_system_config_no_secrets(item.key, item.value)
        try:
            config_gateway.validate_value(item.key, item.value)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        normalized_category = config_gateway.normalize_category(
            item.key, item.category)
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == item.key)
        )
        config = result.scalar_one_or_none()

        if config:
            config.value = item.value
            config.category = normalized_category or item.category
            if item.description:
                config.description = item.description
        else:
            config = SystemConfig(
                key=item.key,
                value=item.value,
                description=item.description,
                category=normalized_category or item.category,
            )
            db.add(config)

    await db.commit()
    return {"message": "配置批量更新成功", "updated_count": len(request.items)}


# ==================== 系统状态监控和日志功能 ====================

import os
import platform
import psutil
from datetime import timedelta


class SystemStatusResponse(BaseModel):
    """系统状态响应"""
    version: str
    environment: str
    uptime: float
    
    # 数据库状态
    database: dict[str, object]
    
    # 缓存状态
    cache: dict[str, object]
    
    # 系统资源
    memory: dict[str, object]
    cpu: dict[str, object]
    disk: dict[str, object]


class SystemLogResponse(BaseModel):
    """系统日志响应"""
    id: str
    level: str
    module: str
    message: str
    details: dict[str, object] | None
    user_id: int | None
    ip_address: str | None
    created_at: datetime


class BackupInfoResponse(BaseModel):
    """备份信息响应"""
    id: str
    name: str
    size: int
    type: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    download_url: str | None


# 模拟系统日志存储（实际项目中应该使用数据库或日志服务）
_system_logs: list[dict] = []
_backup_records: list[dict] = []


@router.get("/status", response_model=SystemStatusResponse, summary="系统状态监控")
async def get_system_status(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取系统运行状态（需要管理员权限）"""
    _ = current_user
    
    # 获取应用启动时间（通过进程启动时间估算）
    process = psutil.Process()
    uptime = time.time() - process.create_time() if hasattr(process, 'create_time') else 0
    
    # 数据库状态检查
    db_status = {"connected": False, "latency": 0}
    try:
        start = time.time()
        await db.execute(select(SystemConfig).limit(1))
        db_status = {"connected": True, "latency": round((time.time() - start) * 1000, 2)}
    except Exception:
        pass
    
    # 缓存状态（Redis）
    cache_status = {"connected": False, "latency": 0}
    try:
        from ...services.cache_service import cache_service
        start = time.time()
        await cache_service.get("health_check")
        cache_status = {"connected": True, "latency": round((time.time() - start) * 1000, 2)}
    except Exception:
        pass
    
    # 内存使用
    memory = psutil.virtual_memory()
    memory_info = {
        "total": memory.total,
        "used": memory.used,
        "free": memory.free,
        "percent": memory.percent
    }
    
    # CPU使用
    cpu_info = {
        "usage": psutil.cpu_percent(interval=0.1),
        "cores": psutil.cpu_count(),
        "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
    }
    
    # 磁盘使用
    disk = psutil.disk_usage('/')
    disk_info = {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": round(disk.used / disk.total * 100, 2)
    }
    
    return SystemStatusResponse(
        version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        uptime=uptime,
        database=db_status,
        cache=cache_status,
        memory=memory_info,
        cpu=cpu_info,
        disk=disk_info
    )


@router.get("/logs", response_model=list[SystemLogResponse], summary="系统日志查询")
async def get_system_logs(
    current_user: Annotated[User, Depends(require_admin)],
    page: int = 1,
    page_size: int = 50,
    level: str | None = None,
    module: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    keyword: str | None = None,
):
    """查询系统日志（需要管理员权限）"""
    _ = current_user
    
    # 这里应该从实际的日志存储中查询
    # 为了演示，返回模拟数据
    logs = []
    for i in range(min(page_size, 20)):
        logs.append(SystemLogResponse(
            id=f"log_{i}",
            level=level or "info",
            module=module or "system",
            message=f"系统日志消息 {i}",
            details=None,
            user_id=None,
            ip_address=None,
            created_at=datetime.now() - timedelta(minutes=i)
        ))
    
    return logs


@router.get("/backups", response_model=list[BackupInfoResponse], summary="备份列表")
async def get_backups(
    current_user: Annotated[User, Depends(require_admin)],
    page: int = 1,
    page_size: int = 20,
):
    """获取备份列表（需要管理员权限）"""
    _ = current_user
    
    # 这里应该从实际的备份存储中查询
    # 为了演示，返回模拟数据
    backups = []
    for i in range(min(page_size, 5)):
        backups.append(BackupInfoResponse(
            id=f"backup_{i}",
            name=f"backup_20240101_{i}.sql",
            size=1024 * 1024 * (i + 1),
            type="full" if i % 2 == 0 else "incremental",
            status="completed",
            created_at=datetime.now() - timedelta(days=i),
            completed_at=datetime.now() - timedelta(days=i) + timedelta(minutes=5),
            download_url=None
        ))
    
    return backups


@router.post("/backups", response_model=BackupInfoResponse, summary="创建备份")
async def create_backup(
    backup_type: str = "full",
    current_user: Annotated[User, Depends(require_admin)] = None,
):
    """创建系统备份（需要管理员权限）"""
    _ = current_user
    
    # 这里应该调用实际的备份服务
    # 为了演示，返回模拟数据
    backup_id = f"backup_{len(_backup_records)}"
    backup = BackupInfoResponse(
        id=backup_id,
        name=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
        size=0,
        type=backup_type,
        status="running",
        created_at=datetime.now(),
        completed_at=None,
        download_url=None
    )
    
    _backup_records.append(backup.model_dump())
    return backup


@router.delete("/backups/{backup_id}", summary="删除备份")
async def delete_backup(
    backup_id: str,
    current_user: Annotated[User, Depends(require_admin)],
):
    """删除备份（需要管理员权限）"""
    _ = current_user
    
    # 这里应该调用实际的备份服务删除备份
    global _backup_records
    _backup_records = [b for b in _backup_records if b.get("id") != backup_id]
    
    return {"message": "备份已删除", "backup_id": backup_id}


import time
