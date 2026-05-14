from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_db
from ..models.user import User
from ..services.feedback_service import FeedbackService
from ..utils.deps import get_current_user

router = APIRouter(prefix="/feedback", tags=["Feedback"])


class CreateFeedbackBody(BaseModel):
    subject: str
    content: str


class UpdateFeedbackBody(BaseModel):
    status: Optional[str] = None
    admin_reply: Optional[str] = None
    admin_id: Optional[int] = None


@router.post("")
async def create_feedback(
    body: CreateFeedbackBody,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    svc = FeedbackService(db)
    ticket = await svc.create_feedback(
        user_id=current_user.id,
        subject=body.subject,
        content=body.content,
    )
    return FeedbackService._ticket_to_dict(ticket)


@router.get("")
async def get_feedback_list(
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = FeedbackService(db)
    return await svc.get_feedback_list(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/admin/tickets/stats")
async def get_feedback_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    svc = FeedbackService(db)
    return await svc.get_feedback_stats()


@router.get("/admin/tickets")
async def get_admin_feedback_list(
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = FeedbackService(db)
    return await svc.get_admin_feedback_list(
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
    )


@router.put("/admin/tickets/{ticket_id}")
async def update_feedback(
    ticket_id: int,
    body: UpdateFeedbackBody,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    svc = FeedbackService(db)
    data = {}
    if body.status is not None:
        data["status"] = body.status
    if body.admin_reply is not None:
        data["admin_reply"] = body.admin_reply
    if body.admin_id is not None:
        data["admin_id"] = body.admin_id
    ticket = await svc.update_feedback(ticket_id=ticket_id, data=data)
    return FeedbackService._ticket_to_dict(ticket)
