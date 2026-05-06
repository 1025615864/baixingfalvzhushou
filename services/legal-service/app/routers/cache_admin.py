"""Redis 缓存集成路由 - 提供缓存管理接口"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.lawyer_service import LawyerService
from ..cache.lawyer_cache import LawyerCache, FirmCache
from ..middleware.auth import get_admin_user, AuthUser
from ..schemas.response import ApiResponse

router = APIRouter()


class CacheStatsResponse(BaseModel):
    keys: int
    memory: Optional[str] = None


class CacheInvalidateRequest(BaseModel):
    pattern: str


@router.get("/stats")
async def get_cache_stats(
    current_user: AuthUser = Depends(get_admin_user),
):
    """获取缓存统计"""
    from main import _redis_client

    if not _redis_client:
        return ApiResponse.success({"status": "no_redis"})

    try:
        info = await _redis_client.info("memory")
        return ApiResponse.success({
            "status": "ok",
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
        })
    except Exception as e:
        return ApiResponse.success({"status": "error", "detail": str(e)})


@router.post("/lawyer/{lawyer_id}/invalidate")
async def invalidate_lawyer_cache(
    lawyer_id: int,
    current_user: AuthUser = Depends(get_admin_user),
):
    """清除律师缓存"""
    from main import _redis_client

    if not _redis_client:
        return ApiResponse.success({"status": "no_redis"})

    cache = LawyerCache(_redis_client)
    await cache.invalidate_lawyer_detail(lawyer_id)
    await cache.invalidate_lawyer_list()

    return ApiResponse.success({"status": "ok", "lawyer_id": lawyer_id})


@router.post("/lawyer-list/invalidate")
async def invalidate_all_lawyer_list_cache(
    current_user: AuthUser = Depends(get_admin_user),
):
    """清除所有律师列表缓存"""
    from main import _redis_client

    if not _redis_client:
        return ApiResponse.success({"status": "no_redis"})

    cache = LawyerCache(_redis_client)
    await cache.invalidate_lawyer_list()

    return ApiResponse.success({"status": "ok"})


@router.post("/firm/{firm_id}/invalidate")
async def invalidate_firm_cache(
    firm_id: int,
    current_user: AuthUser = Depends(get_admin_user),
):
    """清除律所缓存"""
    from main import _redis_client

    if not _redis_client:
        return ApiResponse.success({"status": "no_redis"})

    cache = FirmCache(_redis_client)
    await cache.invalidate_firm_detail(firm_id)
    await cache.invalidate_firm_list()

    return ApiResponse.success({"status": "ok", "firm_id": firm_id})


@router.post("/flush")
async def flush_cache(
    pattern: str = Query("*", description="flush pattern"),
    current_user: AuthUser = Depends(get_admin_user),
):
    """刷新缓存（慎用）"""
    from main import _redis_client

    if not _redis_client:
        return ApiResponse.success({"status": "no_redis"})

    try:
        if pattern == "*":
            await _redis_client.flushdb()
            return ApiResponse.success({"status": "ok", "message": "All cache flushed"})
        else:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await _redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    await _redis_client.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
            return ApiResponse.success({"status": "ok", "deleted": deleted})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/key/{key}")
async def get_cache_key(
    key: str,
    current_user: AuthUser = Depends(get_admin_user),
):
    """查看缓存键值"""
    from main import _redis_client

    if not _redis_client:
        raise HTTPException(status_code=500, detail="Redis not available")

    try:
        value = await _redis_client.get(key)
        if value is None:
            return ApiResponse.success({"key": key, "found": False})
        return ApiResponse.success({"key": key, "found": True, "value": value[:500]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
