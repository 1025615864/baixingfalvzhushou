from __future__ import annotations

import time
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_db
from ..models.user import User
from ..services.points_service import PointsService
from ..utils.deps import get_current_user

router = APIRouter(prefix="/points", tags=["Points"])


class EarnPointsBody(BaseModel):
    points: int
    type: str
    description: Optional[str] = None
    source: Optional[str] = None
    reference_id: Optional[str] = None


_cache: dict[str, tuple[float, object]] = {}


def _get_cached(key: str, ttl: float):
    entry = _cache.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.time() - ts > ttl:
        _cache.pop(key, None)
        return None
    return value


def _set_cached(key: str, value: object) -> None:
    _cache[key] = (time.time(), value)


async def get_points_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PointsService:
    return PointsService(db)


@router.get("/balance")
async def get_points_balance(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PointsService, Depends(get_points_service)],
):
    cache_key = f"balance:{current_user.id}"
    cached = _get_cached(cache_key, 60)
    if cached is not None:
        return cached
    result = await service.get_balance(current_user.id)
    _set_cached(cache_key, result)
    return result


@router.get("/transactions")
async def get_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PointsService, Depends(get_points_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trans_type: Optional[str] = Query(None, alias="type"),
):
    return await service.get_transactions(current_user.id, page, page_size, trans_type)


@router.post("/transactions/earn")
async def earn_points(
    body: EarnPointsBody,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PointsService, Depends(get_points_service)],
):
    result = await service.earn_points(
        user_id=current_user.id,
        points=body.points,
        type=body.type,
        description=body.description,
        source=body.source,
        reference_id=body.reference_id,
    )
    _cache.pop(f"balance:{current_user.id}", None)
    return result


@router.get("/transactions/stats")
async def get_transaction_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PointsService, Depends(get_points_service)],
):
    return await service.get_transaction_stats(current_user.id)


@router.get("/exchange/items")
async def get_exchange_items(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PointsService, Depends(get_points_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
):
    cache_key = f"exchange_items:{page}:{page_size}:{category}"
    cached = _get_cached(cache_key, 300)
    if cached is not None:
        return cached
    result = await service.get_exchange_items(page, page_size, category)
    _set_cached(cache_key, result)
    return result


@router.get("/exchange/items/{item_id}")
async def get_exchange_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PointsService, Depends(get_points_service)],
):
    return await service.get_exchange_item(item_id)


@router.post("/exchange/items/{item_id}/redeem")
async def redeem_exchange_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PointsService, Depends(get_points_service)],
):
    result = await service.redeem_item(current_user.id, item_id)
    _cache.pop(f"balance:{current_user.id}", None)
    return result


@router.get("/exchange/history")
async def get_exchange_history(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PointsService, Depends(get_points_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return await service.get_exchange_history(current_user.id, page, page_size)


@router.get("/rules")
async def get_points_rules(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[PointsService, Depends(get_points_service)],
):
    return await service.get_rules()
