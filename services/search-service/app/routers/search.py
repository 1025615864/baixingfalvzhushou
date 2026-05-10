from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search_service import search_service
from app.database import get_db

router = APIRouter()


@router.get("/")
async def search(
    query: str = Query(..., description="搜索关键词"),
    type: str = Query("all", description="搜索类型: all, news, post, lawyer, knowledge"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None, description="用户ID"),
    db: AsyncSession = Depends(get_db),
):
    return await search_service.search_all(
        session=db,
        query=query,
        search_type=type,
        page=page,
        page_size=page_size,
        user_id=user_id,
    )


@router.get("/by-type/{item_type}")
async def search_by_type(
    item_type: str,
    query: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    valid_types = ("news", "post", "lawyer", "knowledge")
    if item_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid item_type. Must be one of: {', '.join(valid_types)}",
        )
    return await search_service.search_by_type(
        session=db,
        item_type=item_type,
        query=query,
        page=page,
        page_size=page_size,
    )


@router.get("/history")
async def get_search_history(
    user_id: int = Query(..., description="用户ID"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items = await search_service.get_search_history(db, user_id, limit)
    return {"items": items}


@router.get("/suggestions")
async def get_suggestions(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    items = await search_service.get_suggestions(db, query, limit)
    return {"items": items}


@router.get("/hot")
async def get_hot_searches(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    items = await search_service.get_hot_searches(db, limit)
    return {"items": items}
