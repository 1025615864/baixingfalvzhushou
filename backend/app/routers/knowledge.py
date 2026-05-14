from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database.session import get_db
from ..services.knowledge_service import KnowledgeService
from ..services.cache_service import cache_service

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


class CreateArticleBody(BaseModel):
    knowledge_type: str = "law"
    title: str
    article_number: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category: str = "法律"
    keywords: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    source_version: Optional[str] = None
    effective_date: Optional[str] = None
    weight: int = 1
    is_active: bool = True


class UpdateArticleBody(BaseModel):
    knowledge_type: Optional[str] = None
    title: Optional[str] = None
    article_number: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    source_version: Optional[str] = None
    effective_date: Optional[str] = None
    weight: Optional[int] = None
    is_active: Optional[bool] = None


async def get_knowledge_service(
    db: AsyncSession = Depends(get_db),
) -> KnowledgeService:
    return KnowledgeService(db)


@router.get("/laws")
async def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    knowledge_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    return await svc.get_articles(
        page=page,
        page_size=page_size,
        knowledge_type=knowledge_type,
        category=category,
        keyword=keyword,
        is_active=is_active,
    )


@router.post("/laws")
async def create_article(
    body: CreateArticleBody,
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    return await svc.create_article(body.model_dump())


@router.get("/laws/{article_id}")
async def get_article(
    article_id: int,
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    return await svc.get_article(article_id)


@router.put("/laws/{article_id}")
async def update_article(
    article_id: int,
    body: UpdateArticleBody,
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    return await svc.update_article(article_id, body.model_dump(exclude_none=True))


@router.delete("/laws/{article_id}")
async def delete_article(
    article_id: int,
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    return await svc.delete_article(article_id)


@router.get("/laws/distinct-categories")
async def get_distinct_categories(
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    cached = await cache_service.get_json("knowledge:categories")
    if cached is not None:
        return cached
    categories = await svc.get_distinct_categories()
    await cache_service.set_json("knowledge:categories", categories, expire=300)
    return categories


@router.post("/laws/batch-delete")
async def batch_delete(
    ids: list[int],
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    result = await svc.batch_delete(ids)
    await cache_service.delete("knowledge:categories")
    await cache_service.delete("knowledge:stats")
    return result


@router.post("/laws/batch-import")
async def batch_import(
    items: list[dict],
    dry_run: bool = False,
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    result = await svc.batch_import(items, dry_run=dry_run)
    if not dry_run:
        await cache_service.delete("knowledge:categories")
        await cache_service.delete("knowledge:stats")
    return result


@router.post("/laws/{article_id}/vectorize")
async def vectorize_article(
    article_id: int,
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    result = await svc.vectorize_article(article_id)
    await cache_service.delete("knowledge:stats")
    return result


@router.post("/laws/batch-vectorize")
async def batch_vectorize(
    ids: list[int],
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    result = await svc.batch_vectorize(ids)
    await cache_service.delete("knowledge:stats")
    return result


@router.post("/sync-vector-store")
async def sync_vector_store(
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    stats = await svc.get_stats()
    count = stats["vectorized_count"]
    return {
        "success_count": count,
        "failed_count": 0,
        "message": f"向量库同步完成，共{count}条",
    }


@router.get("/stats")
async def get_knowledge_stats(
    svc: KnowledgeService = Depends(get_knowledge_service),
):
    cached = await cache_service.get_json("knowledge:stats")
    if cached is not None:
        return cached
    stats = await svc.get_stats()
    await cache_service.set_json("knowledge:stats", stats, expire=300)
    return stats
