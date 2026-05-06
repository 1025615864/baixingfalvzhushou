"""帖子路由 - Thin Router"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import (
    PostCreateRequest,
    PostUpdateRequest,
    PostResponse,
    PostListResponse,
    LikeResponse,
    FavoriteResponse,
)
from ..services import PostService, ModerationService
from ..middleware import AuthMiddleware, AuthUser
from ..clients import user_service_client
from ..events import event_bus
from ..cache import post_cache

router = APIRouter()

auth_middleware = AuthMiddleware(user_client=user_service_client)
moderation_service = ModerationService()


async def get_post_service(db: AsyncSession = Depends(get_db)) -> PostService:
    return PostService(
        db=db,
        user_client=user_service_client,
        event_bus=event_bus,
        cache=post_cache
    )


@router.get("/", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    sort_by: str = Query("latest", pattern="^(latest|hot|featured)$"),
    service: PostService = Depends(get_post_service)
):
    posts, total = await service.list_posts(
        page=page,
        page_size=page_size,
        category=category,
        sort_by=sort_by
    )
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/search/", response_model=PostListResponse)
async def search_posts(
    q: str = Query(..., min_length=2, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    service: PostService = Depends(get_post_service)
):
    posts, total = await service.search_posts(
        keyword=q,
        page=page,
        page_size=page_size,
        category=category
    )
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/cursor/", response_model=PostListResponse)
async def list_posts_cursor(
    cursor: Optional[str] = Query(None, description="游标（上一页最后一条的ID）"),
    limit: int = Query(20, ge=1, le=50),
    category: Optional[str] = None,
    sort_by: str = Query("latest", pattern="^(latest|hot|featured)$"),
    service: PostService = Depends(get_post_service)
):
    posts, next_cursor, has_more = await service.list_posts_cursor(
        cursor=cursor,
        limit=limit,
        category=category,
        sort_by=sort_by
    )
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=0,
        page=0,
        page_size=limit
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    service: PostService = Depends(get_post_service)
):
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return PostResponse.model_validate(post)


@router.post("/", response_model=PostResponse)
async def create_post(
    request: Request,
    post_data: PostCreateRequest,
    service: PostService = Depends(get_post_service)
):
    current_user = await auth_middleware.get_current_user(request)
    post = await service.create_post(
        user_id=current_user.id,
        title=post_data.title,
        content=post_data.content,
        category=post_data.category,
        tags=post_data.tags,
        moderation_service=moderation_service
    )
    return PostResponse.model_validate(post)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    request: Request,
    post_data: PostUpdateRequest,
    service: PostService = Depends(get_post_service)
):
    current_user = await auth_middleware.get_current_user(request)
    post = await service.update_post(
        post_id=post_id,
        current_user=current_user,
        title=post_data.title,
        content=post_data.content,
        category=post_data.category
    )
    return PostResponse.model_validate(post)


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    request: Request,
    service: PostService = Depends(get_post_service)
):
    current_user = await auth_middleware.get_current_user(request)
    await service.delete_post(post_id, current_user)
    return {"success": True}


@router.post("/{post_id}/like", response_model=LikeResponse)
async def like_post(
    post_id: int,
    request: Request,
    service: PostService = Depends(get_post_service)
):
    current_user = await auth_middleware.get_current_user(request)
    result = await service.like_post(post_id, current_user.id)
    return LikeResponse(**result)


@router.post("/{post_id}/favorite", response_model=FavoriteResponse)
async def favorite_post(
    post_id: int,
    request: Request,
    service: PostService = Depends(get_post_service)
):
    current_user = await auth_middleware.get_current_user(request)
    result = await service.favorite_post(post_id, current_user.id)
    return FavoriteResponse(**result)


@router.get("/user/{user_id}", response_model=PostListResponse)
async def get_user_posts(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: PostService = Depends(get_post_service)
):
    posts, total = await service.get_user_posts(
        user_id=user_id,
        page=page,
        page_size=page_size
    )
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/categories/", response_model=List[str])
async def list_categories(
    service: PostService = Depends(get_post_service)
):
    return ["general", "marriage", "labor", "traffic", "property", "contract", "criminal", "intellectual", "corporate"]
