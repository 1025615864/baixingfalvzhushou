"""AI配置路由"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

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
    return ModelConfigResponse(
        primary_model=settings.llm_model,
        fallback_models=settings.secondary_llm_model.split(",") if settings.secondary_llm_model else [],
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )


@router.get("/rag")
async def get_rag_config():
    return {
        "top_k": settings.rag_top_k,
        "score_threshold": settings.rag_min_similarity,
    }
