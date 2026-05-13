"""向量搜索 API - 提供给AI服务HTTP调用"""
import asyncio
import logging
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.archive_vector_store import search_archive_async
try:
    from services.common.middleware.rate_limit import check_vector_search_rate_limit
except ImportError:
    def check_vector_search_rate_limit(*args, **kwargs):
        return True, 999

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/cases", tags=["向量搜索"])


class VectorSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None
    case_type: Optional[str] = None


class VectorSearchResult(BaseModel):
    id: str
    text: str
    metadata: dict
    distance: float


class VectorSearchResponse(BaseModel):
    results: List[VectorSearchResult]
    total: int
    query: str


@router.post("/vector/search", response_model=VectorSearchResponse)
async def search_vector(
    request: VectorSearchRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """向量搜索档案库（供AI服务HTTP调用）"""
    client_id = http_request.client.host if http_request.client else "unknown"
    is_allowed, remaining = check_vector_search_rate_limit(client_id)
    if not is_allowed:
        raise HTTPException(status_code=429, detail="向量搜索请求过于频繁，请稍后再试")

    try:
        results = await asyncio.wait_for(
            search_archive_async(request.query, request.top_k),
            timeout=15.0
        )

        vector_results = []
        for doc in results:
            vector_results.append(VectorSearchResult(
                id=doc.get("id", ""),
                text=doc.get("content", doc.get("text", "")),
                metadata=doc.get("metadata", {}),
                distance=doc.get("distance", 0.0)
            ))

        return VectorSearchResponse(
            results=vector_results,
            total=len(vector_results),
            query=request.query
        )
    except asyncio.TimeoutError:
        logger.warning(f"Vector search timeout for query: {request.query}")
        raise HTTPException(status_code=504, detail="向量搜索超时，请缩小检索范围或减少top_k参数")
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail="搜索服务暂时不可用")
