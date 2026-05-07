"""搜索路由"""
from typing import Optional
from fastapi import APIRouter, Query, Depends
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
    """全局搜索"""
    return await search_service.search_all(
        session=db,
        query=query,
        search_type=type,
        page=page,
        page_size=page_size,
        user_id=user_id,
    )


@router.get("/suggestions")
async def get_suggestions(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """搜索建议（自动补全）"""
    items = await search_service.get_suggestions(db, query, limit)
    return {"items": items}


@router.get("/hot")
async def get_hot_searches(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """热门搜索"""
    items = await search_service.get_hot_searches(db, limit)
    return {"items": items}
