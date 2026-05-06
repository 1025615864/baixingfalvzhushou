"""向量重建 API"""
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.knowledge_service import KnowledgeService
from services.common.middleware import check_vector_rebuild_rate_limit
from services.common.vector import PGVectorStore, VectorStore, VectorSearchResult

router = APIRouter(prefix="/api/v1/vector", tags=["向量操作"])


class VectorRebuildResponse(BaseModel):
    success: bool
    message: str
    knowledge_id: Optional[int] = None


class VectorRebuildAllResponse(BaseModel):
    success: bool
    total: int
    rebuilt: int
    failed: int
    failed_ids: list[int]


@router.post("/rebuild/{knowledge_id}", response_model=VectorRebuildResponse)
async def rebuild_vector(
    knowledge_id: int,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """重建单个知识的向量索引"""
    client_id = http_request.client.host if http_request.client else "unknown"
    is_allowed, remaining = check_vector_rebuild_rate_limit(client_id)
    if not is_allowed:
        raise HTTPException(status_code=429, detail="向量重建操作限流，请稍后再试")

    service = KnowledgeService(db)
    try:
        result = await service.rebuild_vector(knowledge_id)
        if not result:
            raise HTTPException(status_code=404, detail="知识不存在")
        return VectorRebuildResponse(
            success=True,
            message=f"知识 {knowledge_id} 向量索引重建成功",
            knowledge_id=knowledge_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"向量重建失败: {str(e)}")


@router.post("/rebuild", response_model=VectorRebuildAllResponse)
async def rebuild_all_vectors(
    http_request: Request,
    db: Session = Depends(get_db)
):
    """全量重建所有已发布知识的向量索引"""
    client_id = http_request.client.host if http_request.client else "unknown"
    is_allowed, remaining = check_vector_rebuild_rate_limit(client_id)
    if not is_allowed:
        raise HTTPException(status_code=429, detail="向量重建操作限流，请稍后再试")

    service = KnowledgeService(db)
    try:
        result = await service.rebuild_all_vectors()
        return VectorRebuildAllResponse(
            success=True,
            total=result["total"],
            rebuilt=result["rebuilt"],
            failed=result["failed"],
            failed_ids=result["failed_ids"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"全量向量重建失败: {str(e)}")