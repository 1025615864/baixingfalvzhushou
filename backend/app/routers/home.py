from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..utils.deps import get_current_user_optional
from ..services.home_service import HomeService

router = APIRouter(prefix="/home", tags=["Home"])


async def get_home_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> HomeService:
    return HomeService(db=db, user=user)


@router.get("/data")
async def get_home_data(service: Annotated[HomeService, Depends(get_home_service)]):
    user_id = service.user.id if service.user else None
    return await service.get_home_data(user_id=user_id)


@router.get("/recommendations")
async def get_recommendations(
    service: Annotated[HomeService, Depends(get_home_service)],
    page: int = 1,
    page_size: int = 10,
    recommendation_type: Optional[str] = None,
):
    user_id = service.user.id if service.user else None
    return await service.get_recommendations(
        user_id=user_id,
        page=page,
        page_size=page_size,
        recommendation_type=recommendation_type,
    )


@router.get("/quick-actions")
async def get_quick_actions(service: Annotated[HomeService, Depends(get_home_service)]):
    return await service.get_quick_actions()


@router.get("/stats")
async def get_stats(service: Annotated[HomeService, Depends(get_home_service)]):
    return await service.get_stats()


@router.get("/banners")
async def get_banners(service: Annotated[HomeService, Depends(get_home_service)]):
    return await service.get_banners()


@router.post("/track-click")
async def track_click(
    body: dict,
    request: Request,
    service: Annotated[HomeService, Depends(get_home_service)],
):
    user_id = service.user.id if service.user else None
    data = {
        **body,
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "referrer": request.headers.get("referer"),
    }
    await service.track_click(user_id=user_id, data=data)
    return {"success": True}


@router.post("/interests")
async def set_interests(
    body: dict,
    service: Annotated[HomeService, Depends(get_home_service)],
):
    user_id = service.user.id if service.user else None
    interests = body.get("interests", [])
    return await service.set_interests(user_id=user_id, interests=interests)
