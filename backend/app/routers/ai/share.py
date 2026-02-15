"""AI consultation share routes

Provides share functionality for AI consultations
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...database import get_db
from ...models.consultation import Consultation, ChatMessage
from ...services.report_generator import (
    build_consultation_report_from_export_data,
    generate_consultation_report_pdf,
)
from ...schemas.ai import (
    ShareLinkResponse,
    SharedConsultationResponse,
    SharedMessageResponse,
)
from ...utils.security import create_access_token, decode_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI分享"])


@router.get("/share/{token}", response_model=SharedConsultationResponse)
async def get_shared_consultation(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """获取分享的咨询内容（公开访问）"""
    payload = decode_token(str(token or ""))
    if payload is None:
        raise HTTPException(status_code=401, detail="无效或已过期的分享链接")

    token_type = str(payload.get("type") or "").strip()
    if token_type != "consultation_share":
        raise HTTPException(status_code=401, detail="无效的分享链接")

    # 验证 audience 确保是分享专用 token
    token_aud = str(payload.get("aud") or "").strip()
    if token_aud != "consultation_share":
        raise HTTPException(status_code=401, detail="无效的分享链接")

    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        raise HTTPException(status_code=401, detail="分享链接无效")

    result = await db.execute(select(Consultation).where(Consultation.session_id == session_id))
    consultation = result.scalar_one_or_none()
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.consultation_id == consultation.id)
        .order_by(ChatMessage.created_at)
    )
    messages = messages_result.scalars().all()

    shared_messages: list[SharedMessageResponse] = []
    for msg in messages:
        msg_created_at = msg.created_at
        shared_messages.append(
            SharedMessageResponse(
                role=str(
                    msg.role),
                content=str(
                    msg.content),
                created_at=msg_created_at.isoformat() if msg_created_at is not None else None,
            ))

    consultation_created_at = consultation.created_at
    return SharedConsultationResponse(
        session_id=str(session_id),
        title=cast(str | None, getattr(consultation, "title", None)),
        created_at=consultation_created_at.isoformat(
        ) if consultation_created_at is not None else None,
        messages=shared_messages,
    )
