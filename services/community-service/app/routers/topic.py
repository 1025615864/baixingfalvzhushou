"""话题路由"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.topic_service import TopicService, BestAnswerService
from ..schemas.common_schema import ListResponse, SuccessResponse
from ..middleware.auth import AuthUser
from ..clients import user_service_client
from ..middleware.auth import AuthMiddleware

router = APIRouter()

auth_middleware = AuthMiddleware(user_client=user_service_client)


@router.get("/", response_model=ListResponse)
async def list_topics(
    is_active: Optional[bool] = None,
    is_legal_category: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = TopicService(db)
    topics, total = await service.list_topics(
        is_active=is_active,
        is_legal_category=is_legal_category,
        page=page,
        page_size=page_size
    )
    return ListResponse(
        items=topics,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{topic_name}")
async def get_topic(
    topic_name: str,
    db: AsyncSession = Depends(get_db),
):
    service = TopicService(db)
    topic = await service.get_topic_by_name(topic_name)
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")
    return {"success": True, "data": topic}


@router.get("/{topic_name}/posts", response_model=ListResponse)
async def get_topic_posts(
    topic_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    service = TopicService(db)
    posts, total = await service.get_topic_posts(
        topic_name=topic_name,
        page=page,
        page_size=page_size
    )
    return ListResponse(
        items=posts,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=SuccessResponse)
async def create_topic(
    request: Request,
    name: str,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    sort_order: int = 0,
    is_legal_category: bool = False,
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    if current_user.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    service = TopicService(db)
    topic = await service.create_topic(
        name=name,
        description=description,
        icon=icon,
        sort_order=sort_order,
        is_legal_category=is_legal_category,
        created_by=current_user.id
    )
    return SuccessResponse(success=True, message="话题创建成功")


@router.put("/{topic_id}")
async def update_topic(
    request: Request,
    topic_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    sort_order: Optional[int] = None,
    is_active: Optional[bool] = None,
    is_legal_category: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    service = TopicService(db)
    topic = await service.update_topic(
        topic_id=topic_id,
        current_user=current_user,
        name=name,
        description=description,
        icon=icon,
        sort_order=sort_order,
        is_active=is_active,
        is_legal_category=is_legal_category
    )
    return {"success": True, "message": "话题更新成功", "data": topic}


@router.delete("/{topic_id}", response_model=SuccessResponse)
async def delete_topic(
    request: Request,
    topic_id: int,
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    service = TopicService(db)
    await service.delete_topic(topic_id, current_user)
    return SuccessResponse(success=True, message="话题已禁用")


@router.post("/posts/{post_id}/best-answer")
async def mark_best_answer(
    request: Request,
    post_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
):
    from app.events import event_bus
    current_user = await auth_middleware.get_current_user(request)
    service = BestAnswerService(db, event_bus=event_bus)
    best_answer = await service.mark_best_answer(
        post_id=post_id,
        comment_id=comment_id,
        selected_by=current_user.id
    )
    return {"success": True, "message": "已标记为最佳回答", "data": best_answer}


@router.get("/posts/{post_id}/best-answer")
async def get_best_answer(
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = BestAnswerService(db)
    best_answer = await service.get_best_answer(post_id)
    if not best_answer:
        raise HTTPException(status_code=404, detail="该帖子暂无最佳回答")
    return {"success": True, "data": best_answer}


@router.delete("/posts/{post_id}/best-answer", response_model=SuccessResponse)
async def remove_best_answer(
    request: Request,
    post_id: int,
    db: AsyncSession = Depends(get_db),
):
    current_user = await auth_middleware.get_current_user(request)
    service = BestAnswerService(db)
    await service.remove_best_answer(post_id, current_user)
    return SuccessResponse(success=True, message="已取消最佳回答")
