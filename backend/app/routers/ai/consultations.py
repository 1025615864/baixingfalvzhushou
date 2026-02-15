"""AI consultation routes

Provides AI consultation management endpoints - list, detail, share, export, report
"""
import json
import logging
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists, or_

from ...database import get_db
from ...models.consultation import Consultation, ChatMessage
from ...models.lawfirm import Lawyer
from ...models.user import User
from ...services.report_generator import (
    build_consultation_report_from_export_data,
    generate_consultation_report_pdf,
)
from ...schemas.ai import (
    ConsultationResponse,
    ConsultationListItem,
    MessageResponse,
    ShareLinkResponse,
)
from ...utils.deps import get_current_user
from ...utils.security import create_access_token

router = APIRouter(prefix="/ai/consultations", tags=["AI咨询管理"])

logger = logging.getLogger(__name__)


@router.get("", response_model=list[ConsultationListItem])
async def list_consultations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(max_length=200)] = None,
):
    """
    获取咨询历史列表

    - **skip**: 跳过记录数
    - **limit**: 返回记录数限制
    """
    subquery = (
        select(
            ChatMessage.consultation_id,
            func.count(ChatMessage.id).label('message_count')
        )
        .group_by(ChatMessage.consultation_id)
        .subquery()
    )

    query = (
        select(
            Consultation,
            func.coalesce(subquery.c.message_count, 0).label('message_count')
        )
        .outerjoin(subquery, Consultation.id == subquery.c.consultation_id)
        .where(Consultation.user_id == current_user.id)
    )

    q_norm = str(q or "").strip()
    if q_norm:
        # 转义 LIKE 通配符，防止通配符注入攻击
        q_escaped = q_norm.replace('%', '\\%').replace('_', '\\_')
        q_lower = q_escaped.lower()
        pattern = f"%{q_lower}%"
        title_match = func.lower(
            func.coalesce(
                Consultation.title,
                "")).like(pattern, escape='\\')
        message_match = exists(
            select(1)
            .where(ChatMessage.consultation_id == Consultation.id)
            .where(func.lower(ChatMessage.content).like(pattern, escape='\\'))
        )
        query = query.where(or_(title_match, message_match))

    result = await db.execute(
        query
        .order_by(Consultation.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    rows = cast(list[tuple[Consultation, int]], result.all())
    items: list[ConsultationListItem] = []
    for consultation, message_count in rows:
        items.append(
            ConsultationListItem(
                id=cast(int, cast(object, consultation.id)),
                session_id=cast(str, cast(object, consultation.session_id)),
                title=cast(str | None, cast(object, consultation.title)),
                created_at=cast(
                    datetime, cast(
                        object, consultation.created_at)),
                message_count=int(message_count),
            )
        )

    return items


@router.get("/{session_id}", response_model=ConsultationResponse)
async def get_consultation(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    获取单次咨询详情

    - **session_id**: 会话ID
    """
    result = await db.execute(
        select(Consultation).where(Consultation.session_id == session_id)
    )
    consultation = result.scalar_one_or_none()

    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")

    consultation_user_id = cast(
        int | None, getattr(
            consultation, "user_id", None))
    if consultation_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限访问该咨询记录")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.consultation_id == consultation.id)
        .order_by(ChatMessage.created_at)
    )
    messages = messages_result.scalars().all()

    return ConsultationResponse(
        id=cast(int, cast(object, consultation.id)),
        session_id=cast(str, cast(object, consultation.session_id)),
        title=cast(str | None, cast(object, consultation.title)),
        created_at=cast(datetime, cast(object, consultation.created_at)),
        updated_at=cast(datetime, cast(object, consultation.updated_at)),
        messages=[MessageResponse.model_validate(msg) for msg in messages]
    )


@router.post("/{session_id}/share", response_model=ShareLinkResponse)
async def create_consultation_share_link(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    expires_days: Annotated[int, Query(
        ge=1, le=30, description="分享链接有效期（天）")] = 7,
):
    result = await db.execute(select(Consultation).where(Consultation.session_id == session_id))
    consultation = result.scalar_one_or_none()
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")

    consultation_user_id = cast(
        int | None, getattr(
            consultation, "user_id", None))
    if consultation_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限分享该咨询记录")

    exp_delta = timedelta(days=int(expires_days))
    expires_at = datetime.now(timezone.utc) + exp_delta

    token = create_access_token(
        {
            "type": "consultation_share",
            "session_id": str(session_id),
        },
        expires_delta=exp_delta,
        audience="consultation_share",
    )

    return ShareLinkResponse(
        token=token,
        share_path=f"/share/{token}",
        expires_at=expires_at,
    )


@router.delete("/{session_id}")
async def delete_consultation(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    删除咨询记录

    - **session_id**: 会话ID
    """
    result = await db.execute(
        select(Consultation).where(Consultation.session_id == session_id)
    )
    consultation = result.scalar_one_or_none()

    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")

    consultation_user_id = cast(
        int | None, getattr(
            consultation, "user_id", None))
    if consultation_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限删除该咨询记录")

    await db.delete(consultation)
    await db.commit()

    try:
        from ...services.ai_assistant import get_ai_assistant
        assistant = get_ai_assistant()
        if assistant is not None:
            assistant.clear_session(session_id)
    except Exception:
        logger.exception("Failed to clear AI assistant session")

    return {"message": "删除成功"}


@router.get("/{session_id}/export")
async def export_consultation(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    导出咨询记录为结构化数据（用于前端生成PDF）

    - **session_id**: 会话ID
    """
    result = await db.execute(
        select(Consultation).where(Consultation.session_id == session_id)
    )
    consultation = result.scalar_one_or_none()

    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")

    consultation_user_id = cast(
        int | None, getattr(
            consultation, "user_id", None))
    if consultation_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限访问该咨询记录")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.consultation_id == consultation.id)
        .order_by(ChatMessage.created_at)
    )
    messages = messages_result.scalars().all()

    consultation_created_at = cast(
        datetime | None, getattr(
            consultation, "created_at", None))
    export_data: dict[str, object] = {
        "title": cast(str | None, cast(object, consultation.title)),
        "session_id": cast(str, cast(object, consultation.session_id)),
        "created_at": consultation_created_at.isoformat() if consultation_created_at else None,
        "messages": [],
    }
    export_messages = cast(list[dict[str, object]], export_data["messages"])

    for msg in messages:
        msg_created_at = cast(
            datetime | None, getattr(
                msg, "created_at", None))
        msg_references = cast(str | None, getattr(msg, "references", None))
        msg_data: dict[str, object] = {
            "role": cast(str, cast(object, msg.role)),
            "content": cast(str, cast(object, msg.content)),
            "created_at": msg_created_at.isoformat() if msg_created_at else None,
        }
        if msg_references:
            try:
                parsed = cast(object, json.loads(msg_references))
                if isinstance(parsed, list):
                    msg_data["references"] = cast(object, parsed)
                elif isinstance(parsed, dict):
                    parsed_dict = cast(dict[str, object], parsed)
                    refs = parsed_dict.get("references")
                    if isinstance(refs, list):
                        msg_data["references"] = cast(object, refs)
                    else:
                        msg_data["references"] = []
                    meta_obj = parsed_dict.get("meta")
                    if isinstance(meta_obj, dict):
                        msg_data["references_meta"] = cast(object, meta_obj)
                else:
                    msg_data["references"] = []
            except json.JSONDecodeError:
                msg_data["references"] = []
        export_messages.append(msg_data)

    return export_data


@router.get("/{session_id}/report")
async def consultation_report(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    format: str = Query("pdf", max_length=10),
):
    fmt = str(format or "").strip().lower()
    if fmt != "pdf":
        raise HTTPException(status_code=400, detail="暂不支持该格式")

    export_data = await export_consultation(
        session_id=session_id,
        db=db,
        current_user=current_user,
    )

    user_name = str(getattr(current_user, "nickname", None) or "") or str(
        getattr(current_user, "username", None) or "用户"
    )

    report = build_consultation_report_from_export_data(
        cast(dict[str, object], export_data),
        user_name=user_name,
    )

    try:
        pdf_bytes = generate_consultation_report_pdf(report)
    except RuntimeError as e:
        if str(e) == "PDF_DEPENDENCY_MISSING":
            raise HTTPException(status_code=501, detail="PDF 报告生成依赖未安装")
        raise

    safe_sid = "".join(
        ch
        if (ch.isascii() and (ch.isalnum() or ch in ("-", "_")))
        else "_"
        for ch in str(session_id or "")
    )
    ascii_filename = f"report_{safe_sid or 'session'}.pdf"
    utf8_filename = f"法律咨询报告_{session_id}.pdf"
    quoted_utf8 = urllib.parse.quote(utf8_filename, safe="")
    content_disposition = (
        f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{quoted_utf8}")
    from fastapi import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": content_disposition,
        },
    )


# ==================== 新增功能 ====================

from pydantic import BaseModel, Field
from ...models.consultation import ConsultationStatus, ConsultationCategory
from ...services.ai.consultation_service import ConsultationService


class CreateConsultationRequest(BaseModel):
    """创建咨询请求"""
    title: str | None = Field(None, max_length=200, description="咨询标题")
    category: str = Field(default=ConsultationCategory.GENERAL, description="咨询分类")
    initial_message: str | None = Field(None, max_length=5000, description="初始消息")


class UpdateTitleRequest(BaseModel):
    """更新标题请求"""
    title: str = Field(..., max_length=200, description="新标题")


class UpdateCategoryRequest(BaseModel):
    """更新分类请求"""
    category: str = Field(..., description="新分类")


class MessageFeedbackRequest(BaseModel):
    """消息反馈请求"""
    rating: int = Field(..., ge=1, le=3, description="评分: 1=差评, 2=一般, 3=好评")
    feedback: str | None = Field(None, max_length=500, description="反馈内容")
    is_helpful: bool | None = Field(None, description="是否有帮助")


class TransferToHumanRequest(BaseModel):
    """转人工请求"""
    reason: str | None = Field(None, max_length=500, description="转人工原因")


@router.post("", response_model=ConsultationListItem)
async def create_consultation(
    request: CreateConsultationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    创建新的咨询会话
    """
    consultation = await ConsultationService.create_consultation(
        db=db,
        user_id=current_user.id,
        title=request.title,
        category=request.category,
        initial_message=request.initial_message
    )

    return ConsultationListItem(
        id=consultation.id,
        session_id=consultation.session_id,
        title=consultation.title,
        created_at=consultation.created_at,
        message_count=1 if request.initial_message else 0,
    )


@router.patch("/{session_id}/title")
async def update_consultation_title(
    session_id: str,
    request: UpdateTitleRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    更新咨询会话标题
    """
    consultation = await ConsultationService.get_consultation_by_session_id(db, session_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")
    if consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限修改该咨询记录")

    await ConsultationService.update_consultation_title(db, consultation.id, request.title)
    return {"message": "标题更新成功"}


@router.patch("/{session_id}/category")
async def update_consultation_category(
    session_id: str,
    request: UpdateCategoryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    更新咨询会话分类
    """
    consultation = await ConsultationService.get_consultation_by_session_id(db, session_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")
    if consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限修改该咨询记录")

    await ConsultationService.update_consultation_category(db, consultation.id, request.category)
    return {"message": "分类更新成功"}


@router.post("/{session_id}/archive")
async def archive_consultation(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    reason: str | None = None,
):
    """
    归档咨询会话
    """
    consultation = await ConsultationService.get_consultation_by_session_id(db, session_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")
    if consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限修改该咨询记录")

    await ConsultationService.archive_consultation(db, consultation.id, reason)
    return {"message": "归档成功"}


@router.post("/{session_id}/transfer")
async def transfer_to_human(
    session_id: str,
    request: TransferToHumanRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    转人工咨询

    将AI咨询转接给人工律师处理
    """
    consultation = await ConsultationService.get_consultation_by_session_id(db, session_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")
    if consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限操作该咨询记录")

    # 实现律师智能分配逻辑
    # 1. 获取咨询消息内容用于匹配
    messages = await ConsultationService.get_messages(db, consultation.id, limit=10)

    # 2. 构建查询文本
    query_text = ""
    if consultation.title:
        query_text += consultation.title + " "
    for msg in messages:
        if msg.role == "user" and msg.content:
            query_text += msg.content + " "

    query_text = query_text.strip()

    lawyer_id = None

    # 3. 尝试使用智能匹配服务
    if query_text:
        try:
            from ...services.lawyer_matching_service_enhanced import get_lawyer_matching_service_enhanced
            matching_service = get_lawyer_matching_service_enhanced()
            matched_lawyers = await matching_service.recommend_lawyers(
                db, query_text, limit=5
            )
            if matched_lawyers:
                # 选择匹配度最高的律师
                lawyer_id = matched_lawyers[0].lawyer_id
                logger.info(f"Smart lawyer match: consultation={consultation.id}, lawyer={lawyer_id}, score={matched_lawyers[0].overall_score}")
        except Exception as e:
            logger.warning(f"Lawyer matching failed, will use fallback: {e}")

    # 4. 如果智能匹配失败，使用轮询策略获取可用律师
    if lawyer_id is None:
        lawyer_result = await db.execute(
            select(Lawyer)
            .where(Lawyer.is_verified == True, Lawyer.is_active == True)
            .order_by(func.random())
            .limit(1)
        )
        available_lawyer = lawyer_result.scalar_one_or_none()

        if available_lawyer:
            lawyer_id = available_lawyer.id
            logger.info(f"Fallback lawyer assignment: consultation={consultation.id}, lawyer={lawyer_id}")
        else:
            # 没有可用律师时使用默认值
            lawyer_id = 1
            logger.warning(f"No available lawyers, using default: consultation={consultation.id}")

    await ConsultationService.transfer_to_human(
        db, consultation.id, lawyer_id, request.reason
    )
    return {"message": "已转接人工咨询"}


@router.post("/{session_id}/messages/{message_id}/feedback")
async def add_message_feedback(
    session_id: str,
    message_id: int,
    request: MessageFeedbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    添加消息反馈
    """
    consultation = await ConsultationService.get_consultation_by_session_id(db, session_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")
    if consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限操作该咨询记录")

    await ConsultationService.add_message_feedback(
        db, message_id, request.rating, request.feedback, request.is_helpful
    )
    return {"message": "反馈提交成功"}


@router.get("/{session_id}/stats")
async def get_consultation_stats(
    session_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    获取咨询会话统计
    """
    consultation = await ConsultationService.get_consultation_by_session_id(db, session_id)
    if not consultation:
        raise HTTPException(status_code=404, detail="咨询记录不存在")
    if consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限访问该咨询记录")

    return {
        "message_count": consultation.message_count,
        "total_tokens": consultation.total_tokens,
        "category": consultation.category,
        "status": consultation.status,
        "created_at": consultation.created_at.isoformat() if consultation.created_at else None,
        "updated_at": consultation.updated_at.isoformat() if consultation.updated_at else None,
    }


@router.get("/user/stats")
async def get_user_consultation_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    获取用户咨询统计
    """
    stats = await ConsultationService.get_consultation_stats(db, current_user.id)
    return stats
