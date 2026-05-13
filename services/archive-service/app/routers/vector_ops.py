"""向量操作 API"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.archive_service import ArchiveService
try:
    from services.common.middleware import check_vector_rebuild_rate_limit
except ImportError:
    def check_vector_rebuild_rate_limit(*args, **kwargs):
        return True, 999

try:
    from services.common.vector import PGVectorStore, VectorStore, VectorSearchResult
except ImportError:
    class VectorSearchResult:
        def __init__(self, id="", text="", metadata=None, distance=0.0):
            self.id = id
            self.text = text
            self.metadata = metadata or {}
            self.distance = distance

    class VectorStore:
        pass

    class PGVectorStore(VectorStore):
        pass

router = APIRouter(prefix="/api/v1/vector", tags=["向量操作"])


class VectorRebuildResponse(BaseModel):
    case_id: int
    status: str
    vector_id: str = None
    error: str = None


class VectorRebuildAllResponse(BaseModel):
    total: int
    success_count: int
    failed_count: int
    results: list


def get_archive_service(db: Session = Depends(get_db)) -> ArchiveService:
    return ArchiveService(db)


@router.post("/rebuild", response_model=VectorRebuildAllResponse)
async def rebuild_all_vectors(
    http_request: Request,
    service: ArchiveService = Depends(get_archive_service)
):
    """全量重建所有已发布案例的向量索引"""
    client_id = http_request.client.host if http_request.client else "unknown"
    is_allowed, remaining = check_vector_rebuild_rate_limit(client_id)
    if not is_allowed:
        raise HTTPException(status_code=429, detail="向量重建操作限流，请稍后再试")

    result = service.rebuild_all_vectors()
    return result


@router.post("/rebuild/{case_id}", response_model=VectorRebuildResponse)
async def rebuild_vector(
    case_id: int,
    http_request: Request,
    service: ArchiveService = Depends(get_archive_service)
):
    """重建单个案例的向量索引"""
    client_id = http_request.client.host if http_request.client else "unknown"
    is_allowed, remaining = check_vector_rebuild_rate_limit(client_id)
    if not is_allowed:
        raise HTTPException(status_code=429, detail="向量重建操作限流，请稍后再试")

    try:
        result = service.rebuild_vector(case_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
