from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.deps import get_current_user_optional
from app.services.search_service import search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def global_search(
    q: str = Query(default=""),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    results = await search_service.global_search(db, query=q, limit=limit)
    try:
        await search_service.record_search(db, keyword=q)
    except Exception:
        pass
    return results


@router.get("/suggestions")
async def search_suggestions(
    q: str = Query(default=""),
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    suggestions = await search_service.search_suggestions(db, query=q, limit=limit)
    return {"suggestions": suggestions}


@router.get("/hot")
async def hot_keywords(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    keywords = await search_service.get_hot_keywords(db, limit=limit)
    return {"keywords": [kw["keyword"] for kw in keywords]}


@router.get("/history")
async def search_history(
    limit: int = Query(default=10, ge=1, le=50),
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        return {"history": []}
    history = await search_service.get_user_search_history(db, user_id=current_user.id, limit=limit)
    return {"history": history}


@router.delete("/history")
async def clear_search_history(
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        return {"message": "未登录"}
    await search_service.clear_user_search_history(db, user_id=current_user.id)
    return {"message": "搜索历史已清除"}
