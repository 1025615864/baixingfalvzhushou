"""AI配置路由"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..config.settings import get_settings

router = APIRouter()
settings = get_settings()


class ModelConfigResponse(BaseModel):
    primary_model: str
    fallback_models: list
    temperature: float
    max_tokens: int


@router.get("/models", response_model=ModelConfigResponse)
async def get_model_config():
    """获取模型配置"""
    return ModelConfigResponse(
        primary_model=settings.openai_model,
        fallback_models=settings.openai_fallback_models.split(",") if settings.openai_fallback_models else [],
        temperature=0.3,
        max_tokens=4096,
    )


@router.get("/rag")
async def get_rag_config():
    """获取RAG配置"""
    return {
        "top_k": settings.rag_top_k,
        "score_threshold": settings.rag_score_threshold,
    }
