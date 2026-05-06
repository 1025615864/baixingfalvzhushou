"""Embedding服务 - 共享Embedding模型微服务"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import numpy as np

from app.config.settings import get_settings
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.middleware.internal_auth import verify_internal_api_key

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting embedding service...")
    service = get_embedding_service()
    yield
    logger.info("Shutting down embedding service...")


app = FastAPI(
    title="Embedding Service",
    description="共享Embedding模型微服务",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str
    device: str


_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查 - 公开端点"""
    service = get_embedding_service()
    return HealthResponse(
        status="healthy",
        model_loaded=service.is_model_loaded(),
        model_name=service.model_name,
        device=service.device
    )


@app.get("/health/ready")
async def readiness_check():
    """就绪检查 - 公开端点"""
    service = get_embedding_service()
    if not service.is_model_loaded():
        return {"status": "not_ready", "reason": "model not loaded"}
    return {"status": "ready"}


@app.post("/embed/texts", response_model=EmbedTextResponse)
async def embed_texts(
    request: EmbedTextRequest,
    api_key: str = Depends(verify_internal_api_key)
):
    """批量文本Embedding - 需要内部API Key"""
    try:
        service = get_embedding_service()
        embeddings = service.encode(request.texts, normalize=request.normalize)

        return EmbedTextResponse(
            embeddings=embeddings.tolist(),
            model=service.model_name,
            dimension=service.embedding_dim,
            usage_count=len(request.texts)
        )
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed/query", response_model=EmbedQueryResponse)
async def embed_query(
    request: EmbedQueryRequest,
    api_key: str = Depends(verify_internal_api_key)
):
    """单条查询Embedding - 需要内部API Key"""
    try:
        service = get_embedding_service()
        embedding = service.encode_query(request.query, normalize=request.normalize)

        return EmbedQueryResponse(
            embedding=embedding.tolist(),
            model=service.model_name,
            dimension=service.embedding_dim
        )
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """服务信息 - 公开端点"""
    service = get_embedding_service()
    return {
        "service": "embedding-service",
        "version": "1.0.0",
        "model": service.model_name,
        "dimension": service.embedding_dim,
        "device": service.device,
        "model_loaded": service.is_model_loaded()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=settings.ENVIRONMENT == "development"
    )
