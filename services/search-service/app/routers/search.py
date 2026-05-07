"""搜索路由"""
from typing import List, Optional

from fastapi import APIRouter, Query

from app.services.search_service import search_service

router = APIRouter()


@router.get("/")
async def search(
    query: str = Query(..., description="搜索关键词"),
    type: str = Query("all", description="搜索类型: all, news, post, lawyer, knowledge"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """全局搜索"""
    return await search_service.search_all(
        query=query,
        search_type=type,
        page=page,
        page_size=page_size,
    )


@router.get("/suggestions")
async def get_suggestions(
    query: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50),
):
    """搜索建议（自动补全）"""
    items = await search_service.get_suggestions(query, limit)
    return {"items": items}


@router.get("/hot")
async def get_hot_searches(
    limit: int = Query(10, ge=1, le=50),
):
    """热门搜索"""
    items = await search_service.get_hot_searches(limit)
    return {"items": items}
