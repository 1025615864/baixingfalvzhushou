"""收藏路由"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services import FavoriteService, PostService
from ..middleware import AuthMiddleware
from ..clients import user_service_client
from ..events import event_bus
from ..schemas import PostResponse

router = APIRouter()

auth_middleware = AuthMiddleware(user_client=user_service_client)


async def get_favorite_service(db: AsyncSession = Depends(get_db)) -> FavoriteService:
    return FavoriteService(db)


async def get_post_service(db: AsyncSession = Depends(get_db)) -> PostService:
    return PostService(db=db, user_client=user_service_client, event_bus=event_bus, cache=None)


@router.get("/")
async def get_my_favorites(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: FavoriteService = Depends(get_favorite_service)
):
    current_user = await auth_middleware.get_current_user(request)
    items, total = await service.get_user_favorites(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    return {
        "items": [
            {
                "post": PostResponse.model_validate(item["post"]),
                "favorited_at": item["favorited_at"]
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{post_id}/status")
async def check_favorite_status(
    post_id: int,
    request: Request,
    service: FavoriteService = Depends(get_favorite_service)
):
    current_user = await auth_middleware.get_current_user(request)
    is_favorited = await service.is_favorited(post_id, current_user.id)
    return {"is_favorited": is_favorited}
