"""律师咨询留言路由"""

from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...database import get_db
from ...models.lawfirm import LawyerConsultation, LawyerConsultationMessage
from ...models.user import User
from ...schemas.lawfirm import ConsultationMessageCreate, ConsultationMessageResponse, ConsultationMessageListResponse
from ...services.lawfirm_service import LawyerConsultationService, ConsultationMessageService
from ...utils.deps import get_current_user

router = APIRouter(prefix="/consultations", tags=["咨询留言"])


@router.post("/{consultation_id}/messages",
             response_model=ConsultationMessageResponse, summary="发送留言")
async def send_message(
    consultation_id: int,
    data: ConsultationMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """发送咨询留言"""
    consultation = await LawyerConsultationService.get_by_id(db, consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询不存在")

    # 检查权限：只有咨询的用户或律师可以发送留言
    lawyer_user_id = consultation.lawyer.user_id if consultation.lawyer.user_id else None
    if consultation.user_id != current_user.id and lawyer_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")

    # 检查咨询状态：允许pending状态的咨询发送留言
    if consultation.status not in ["pending", "accepted", "in_progress"]:
        raise HTTPException(status_code=400, detail="咨询状态不允许发送留言")

    # 确定发送者角色
    sender_role = "user" if consultation.user_id == current_user.id else "lawyer"

    message = await ConsultationMessageService.create(
        db,
        consultation_id=consultation_id,
        sender_id=current_user.id,
        sender_type=sender_role,
        content=data.content
    )

    return ConsultationMessageResponse(
        id=message.id,
        consultation_id=message.consultation_id,
        sender_user_id=message.sender_user_id,
        sender_role=message.sender_role,
        content=message.content,
        created_at=message.created_at,
        sender_name=current_user.nickname or current_user.username
    )


@router.get("/{consultation_id}/messages",
            response_model=ConsultationMessageListResponse, summary="获取留言列表")
async def get_messages(
    consultation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """获取咨询留言列表"""
    consultation = await LawyerConsultationService.get_by_id(db, consultation_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询不存在")

    # 检查权限：只有咨询的用户或律师可以查看留言
    lawyer_user_id = consultation.lawyer.user_id if consultation.lawyer.user_id else None
    if consultation.user_id != current_user.id and lawyer_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")

    # 获取留言列表
    messages = await ConsultationMessageService.get_messages(db, consultation_id)

    # 构建响应
    items = []
    for message in messages:
        items.append(ConsultationMessageResponse(
            id=message.id,
            consultation_id=message.consultation_id,
            sender_user_id=message.sender_user_id,
            sender_role=message.sender_role,
            content=message.content,
            created_at=message.created_at,
            sender_name=message.sender.nickname or message.sender.username
        ))

    return ConsultationMessageListResponse(
        items=items,
        total=len(items),
        page=page,
        page_size=page_size
    )
