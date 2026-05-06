"""评论路由 - Thin Router"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import (
    CommentCreateRequest,
    CommentResponse,
    CommentListResponse,
)
from ..services import CommentService
from ..middleware import AuthMiddleware
from ..clients import user_service_client
from ..events import event_bus

router = APIRouter()

auth_middleware = AuthMiddleware(user_client=user_service_client)


async def get_comment_service(db: AsyncSession = Depends(get_db)) -> CommentService:
    return CommentService(
        db=db,
        user_client=user_service_client,
        event_bus=event_bus
    )


@router.get("/{post_id}/comments", response_model=CommentListResponse)
async def list_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    nested: bool = Query(True),
    service: CommentService = Depends(get_comment_service)
):
    comments, total = await service.get_comments(
        post_id=post_id,
        page=page,
        page_size=page_size,
        nested=nested
    )

    if nested:
        return CommentListResponse(
            items=[CommentResponse(**c) for c in comments],
            total=total,
            page=page,
            page_size=page_size
        )

    return CommentListResponse(
        items=[CommentResponse.model_validate(c) for c in comments],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    request: Request,
    comment_data: CommentCreateRequest,
    service: CommentService = Depends(get_comment_service)
):
    current_user = await auth_middleware.get_current_user(request)
    comment = await service.create_comment(
        post_id=post_id,
        user_id=current_user.id,
        content=comment_data.content,
        parent_id=comment_data.parent_id,
        reply_to_user_id=comment_data.reply_to_user_id
    )
    return CommentResponse.model_validate(comment)


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    request: Request,
    service: CommentService = Depends(get_comment_service)
):
    current_user = await auth_middleware.get_current_user(request)
    await service.delete_comment(comment_id, current_user)
    return {"success": True}


@router.post("/{comment_id}/like")
async def like_comment(
    comment_id: int,
    request: Request,
    service: CommentService = Depends(get_comment_service)
):
    current_user = await auth_middleware.get_current_user(request)
    result = await service.like_comment(comment_id, current_user.id)
    return result
