"""智能匹配路由"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.matching_service import MatchingService
from ..schemas.response import ApiResponse

router = APIRouter()


@router.get("/match")
async def match_lawyers(
    category: str = Query(..., description="案件领域"),
    description: Optional[str] = Query(None, description="案件描述"),
    limit: int = Query(5, ge=1, le=20),
    user_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """智能匹配律师"""
    service = MatchingService(db)
    result = await service.match_lawyers(
        category=category,
        description=description,
        limit=limit,
        user_id=user_id,
    )
    return ApiResponse.success(result)


@router.post("/match-for-consultation")
async def match_for_consultation(
    consultation_id: int,
    limit: int = 5,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """为特定咨询匹配律师"""
    service = MatchingService(db)
    items = await service.match_for_consultation(consultation_id, limit)
    return ApiResponse.success({"items": items, "total": len(items)})


@router.get("/recommended")
async def get_recommended(
    user_id: Optional[int] = Query(None),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取推荐律师"""
    service = MatchingService(db)
    items = await service.get_recommended_lawyers(user_id=user_id, limit=limit)
    return ApiResponse.success({"items": items, "total": len(items)})