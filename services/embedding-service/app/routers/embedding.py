import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.middleware.internal_auth import verify_internal_api_key
from app.services.embedding_service import EmbeddingService, get_embedding_service

router = APIRouter()
logger = logging.getLogger(__name__)


class EmbedTextRequest(BaseModel):
    texts: List[str]
    normalize: bool = True


class EmbedQueryRequest(BaseModel):
    query: str
    normalize: bool = True


class EmbedTextResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimension: int
    usage_count: int


class EmbedQueryResponse(BaseModel):
    embedding: List[float]
    model: str
    dimension: int


class BatchEmbedRequest(BaseModel):
    texts: List[str]
    batch_size: int = Field(default=32, ge=1, le=512)
    normalize: bool = True


class BatchEmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimension: int
    total_count: int
    batch_size: int
    batch_count: int


class SimilarityRequest(BaseModel):
    text1: str
    text2: str
    normalize: bool = True


class SimilarityResponse(BaseModel):
    similarity: float
    model: str
    dimension: int


class SearchRequest(BaseModel):
    query: str
    candidates: List[str]
    top_k: int = Field(default=5, ge=1, le=100)
    normalize: bool = True


class SearchResult(BaseModel):
    index: int
    text: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    model: str
    dimension: int
    total_candidates: int


@router.post("/texts", response_model=EmbedTextResponse)
async def embed_texts(
    request: EmbedTextRequest,
    api_key: str = Depends(verify_internal_api_key),
):
    try:
        service = get_embedding_service()
        embeddings = service.encode(request.texts, normalize=request.normalize)
        return EmbedTextResponse(
            embeddings=embeddings.tolist(),
            model=service.model_name,
            dimension=service.embedding_dim,
            usage_count=len(request.texts),
        )
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=EmbedQueryResponse)
async def embed_query(
    request: EmbedQueryRequest,
    api_key: str = Depends(verify_internal_api_key),
):
    try:
        service = get_embedding_service()
        embedding = service.encode_query(request.query, normalize=request.normalize)
        return EmbedQueryResponse(
            embedding=embedding.tolist(),
            model=service.model_name,
            dimension=service.embedding_dim,
        )
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchEmbedResponse)
async def batch_embed(
    request: BatchEmbedRequest,
    api_key: str = Depends(verify_internal_api_key),
):
    try:
        service = get_embedding_service()
        embeddings = service.batch_encode(
            request.texts,
            batch_size=request.batch_size,
            normalize=request.normalize,
        )
        batch_count = (len(request.texts) + request.batch_size - 1) // request.batch_size
        return BatchEmbedResponse(
            embeddings=embeddings.tolist(),
            model=service.model_name,
            dimension=service.embedding_dim,
            total_count=len(request.texts),
            batch_size=request.batch_size,
            batch_count=batch_count,
        )
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similarity", response_model=SimilarityResponse)
async def compute_similarity(
    request: SimilarityRequest,
    api_key: str = Depends(verify_internal_api_key),
):
    try:
        service = get_embedding_service()
        emb1 = service.encode(request.text1, normalize=request.normalize)
        emb2 = service.encode(request.text2, normalize=request.normalize)
        score = service.similarity(emb1, emb2)
        return SimilarityResponse(
            similarity=score,
            model=service.model_name,
            dimension=service.embedding_dim,
        )
    except Exception as e:
        logger.error(f"Similarity computation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def vector_search(
    request: SearchRequest,
    api_key: str = Depends(verify_internal_api_key),
):
    try:
        service = get_embedding_service()
        results = service.search(
            query=request.query,
            candidates=request.candidates,
            top_k=request.top_k,
            normalize=request.normalize,
        )
        return SearchResponse(
            query=request.query,
            results=[
                SearchResult(index=r["index"], text=r["text"], score=r["score"])
                for r in results
            ],
            model=service.model_name,
            dimension=service.embedding_dim,
            total_candidates=len(request.candidates),
        )
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
