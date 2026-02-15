"""论坛律师邀请相关路由"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.forum import ForumLawyerInvitation
from ...models.lawfirm import Lawyer
from ...models.user import User
from ...schemas.forum import LawyerInvitationCreate, LawyerInvitationListResponse, LawyerInvitationResponse
from ...services.forum_service import forum_service
from ...utils.deps import get_current_user
from .common import _create_notification, _get_current_lawyer

router = APIRouter()


@router.post("/posts/{post_id}/invite-lawyer",
             response_model=LawyerInvitationResponse, summary="邀请律师解答帖子")
async def invite_lawyer_to_post(
    post_id: int,
    invitation_data: LawyerInvitationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    post = await forum_service.get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在")
    lawyer_result = await db.execute(
        select(Lawyer).where(
            and_(
                Lawyer.id == invitation_data.lawyer_id,
                Lawyer.is_verified,
                Lawyer.is_active)
        )
    )
    lawyer = lawyer_result.scalar_one_or_none()
    if not lawyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="律师不存在或未认证")
    existing_result = await db.execute(
        select(ForumLawyerInvitation).where(
            and_(
                ForumLawyerInvitation.post_id == post_id,
                ForumLawyerInvitation.lawyer_id == invitation_data.lawyer_id,
                ForumLawyerInvitation.status.in_(["pending", "accepted"]),
            )
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已邀请该律师或律师已接受邀请")
    invitation = ForumLawyerInvitation(
        post_id=post_id,
        lawyer_id=invitation_data.lawyer_id,
        invited_by=current_user.id,
        status="pending",
        message=invitation_data.message,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)
    content = f"用户邀请您解答帖子：{post.title}"
    link = f"/forum/post/{int(post_id)}"
    await _create_notification(
        db,
        user_id=int(
            lawyer.user_id) if lawyer.user_id else int(
            invitation_data.lawyer_id),
        title="您有新的论坛邀请",
        content=content,
        link=link,
        related_post_id=int(post_id),
    )
    await db.commit()
    return LawyerInvitationResponse.model_validate(invitation)


@router.get("/lawyer/invitations",
            response_model=LawyerInvitationListResponse, summary="律师查看邀请列表")
async def get_lawyer_invitations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_param: Annotated[
        str | None,
        Query(
            alias="status",
            description="筛选状态：all/pending/accepted/declined/expired"),
    ] = None,
):
    lawyer = await _get_current_lawyer(db, current_user)
    base_filter = and_(ForumLawyerInvitation.lawyer_id == lawyer.id)
    status_filter = (status_param or "all").strip().lower()
    if status_filter != "all":
        if status_filter not in ("pending", "accepted", "declined", "expired"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="status 仅支持 all / pending / accepted / declined / expired",
            )
        base_filter = and_(
            base_filter,
            ForumLawyerInvitation.status == status_filter)
    total_result = await db.execute(select(func.count(ForumLawyerInvitation.id)).where(base_filter))
    total = int(total_result.scalar() or 0)
    query = (
        select(ForumLawyerInvitation)
        .where(base_filter)
        .order_by(desc(ForumLawyerInvitation.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    invitations = result.scalars().all()
    items = [LawyerInvitationResponse.model_validate(
        inv) for inv in invitations]
    return LawyerInvitationListResponse(
        items=items, total=total, page=page, page_size=page_size)


@router.post("/lawyer/invitations/{invitation_id}/accept", summary="律师接受邀请")
async def accept_lawyer_invitation(
    invitation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lawyer = await _get_current_lawyer(db, current_user)
    result = await db.execute(
        select(ForumLawyerInvitation).where(
            and_(ForumLawyerInvitation.id == invitation_id,
                 ForumLawyerInvitation.lawyer_id == lawyer.id)
        )
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邀请不存在")
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"邀请状态为 {invitation.status}，无法接受",
        )
    if invitation.expires_at and invitation.expires_at < datetime.now(
            timezone.utc):
        invitation.status = "expired"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请已过期")
    invitation.status = "accepted"
    invitation.responded_at = datetime.now(timezone.utc)
    await db.commit()
    content = "律师已接受您对帖子的邀请"
    link = f"/forum/post/{int(invitation.post_id)}"
    await _create_notification(
        db,
        user_id=int(invitation.invited_by),
        title="律师已接受您的邀请",
        content=content,
        link=link,
        related_post_id=int(invitation.post_id),
    )
    await db.commit()
    return {"message": "已接受邀请"}


@router.post("/lawyer/invitations/{invitation_id}/decline", summary="律师拒绝邀请")
async def decline_lawyer_invitation(
    invitation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    lawyer = await _get_current_lawyer(db, current_user)
    result = await db.execute(
        select(ForumLawyerInvitation).where(
            and_(ForumLawyerInvitation.id == invitation_id,
                 ForumLawyerInvitation.lawyer_id == lawyer.id)
        )
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邀请不存在")
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"邀请状态为 {invitation.status}，无法拒绝",
        )
    invitation.status = "declined"
    invitation.responded_at = datetime.now(timezone.utc)
    await db.commit()
    content = "律师已拒绝您对帖子的邀请"
    link = f"/forum/post/{int(invitation.post_id)}"
    await _create_notification(
        db,
        user_id=int(invitation.invited_by),
        title="律师已拒绝您的邀请",
        content=content,
        link=link,
        related_post_id=int(invitation.post_id),
    )
    await db.commit()
    return {"message": "已拒绝邀请"}
