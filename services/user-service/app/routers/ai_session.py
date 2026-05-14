"""AI会话API路由"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models_ai import AISession, AIMessage

router = APIRouter(prefix="/api/v1/ai", tags=["AI会话"])


class SessionCreateRequest(BaseModel):
    user_id: int
    title: Optional[str] = None
    model: Optional[str] = None


class SessionCreateResponse(BaseModel):
    session_id: str
    user_id: int
    title: Optional[str]
    created_at: datetime


class SessionUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    session_id: str
    user_id: int
    title: Optional[str]
    status: str
    total_messages: int
    total_tokens: int
    model: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
    page: int
    page_size: int


class MessageCreateRequest(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    intent: Optional[str] = None
    search_query: Optional[str] = None
    retrieved_docs: Optional[str] = None
    draft_response: Optional[str] = None
    hallucination_feedback: Optional[str] = None
    tokens: int = 0
    latency_ms: Optional[int] = None
    error_flag: bool = False
    error_message: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    message_id: str
    session_id: int
    role: str
    content: str
    intent: Optional[str]
    search_query: Optional[str]
    retrieved_docs: Optional[str]
    draft_response: Optional[str]
    hallucination_feedback: Optional[str]
    tokens: int
    latency_ms: Optional[int]
    error_flag: bool
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int


class SessionStatsResponse(BaseModel):
    total_sessions: int
    total_messages: int
    total_tokens: int
    active_sessions: int
    average_messages_per_session: float


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(
    request: SessionCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建新会话"""
    session_id = str(uuid.uuid4())
    session = AISession(
        session_id=session_id,
        user_id=request.user_id,
        title=request.title or f"新会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        model=request.model
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionCreateResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取会话详情"""
    result = await db.execute(
        select(AISession).where(
            AISession.session_id == session_id,
            AISession.is_deleted == False
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新会话"""
    result = await db.execute(
        select(AISession).where(
            AISession.session_id == session_id,
            AISession.is_deleted == False
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.title is not None:
        session.title = request.title
    if request.status is not None:
        session.status = request.status

    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除会话(软删除)"""
    result = await db.execute(
        select(AISession).where(
            AISession.session_id == session_id,
            AISession.is_deleted == False
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_deleted = True
    session.deleted_at = datetime.now(timezone.utc)
    session.status = "deleted"

    await db.execute(
        select(AIMessage).where(
            AIMessage.session_id == session.id,
            AIMessage.is_deleted == False
        )
    )
    msg_result = await db.execute(
        select(AIMessage).where(
            AIMessage.session_id == session.id,
            AIMessage.is_deleted == False
        )
    )
    messages = msg_result.scalars().all()
    for msg in messages:
        msg.is_deleted = True
        msg.deleted_at = datetime.now(timezone.utc)

    await db.commit()
    return {"message": "Session deleted"}


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取用户会话列表"""
    query = select(AISession).where(
        AISession.user_id == user_id,
        AISession.is_deleted == False
    )

    if status:
        query = query.where(AISession.status == status)

    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(desc(AISession.updated_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return SessionListResponse(
        sessions=sessions,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def create_message(
    session_id: str,
    request: MessageCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建新消息"""
    result = await db.execute(
        select(AISession).where(
            AISession.session_id == session_id,
            AISession.is_deleted == False
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message_id = str(uuid.uuid4())
    message = AIMessage(
        session_id=session.id,
        message_id=message_id,
        role=request.role,
        content=request.content,
        intent=request.intent,
        search_query=request.search_query,
        retrieved_docs=request.retrieved_docs,
        draft_response=request.draft_response,
        hallucination_feedback=request.hallucination_feedback,
        tokens=request.tokens,
        latency_ms=request.latency_ms,
        error_flag=request.error_flag,
        error_message=request.error_message
    )
    db.add(message)

    session.total_messages += 1
    session.total_tokens += request.tokens
    session.last_message_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(message)
    return message


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def list_messages(
    session_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """获取会话消息列表"""
    result = await db.execute(
        select(AISession).where(
            AISession.session_id == session_id,
            AISession.is_deleted == False
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    count_query = select(func.count()).select_from(AIMessage).where(
        AIMessage.session_id == session.id,
        AIMessage.is_deleted == False
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    messages_query = select(AIMessage).where(
        AIMessage.session_id == session.id,
        AIMessage.is_deleted == False
    ).order_by(AIMessage.created_at)

    messages_query = messages_query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(messages_query)
    messages = result.scalars().all()

    return MessageListResponse(
        messages=messages,
        total=total
    )


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """获取会话历史(简化格式,用于AI上下文)"""
    result = await db.execute(
        select(AISession).where(
            AISession.session_id == session_id,
            AISession.is_deleted == False
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_result = await db.execute(
        select(AIMessage).where(
            AIMessage.session_id == session.id,
            AIMessage.is_deleted == False
        ).order_by(AIMessage.created_at.desc()).limit(limit)
    )
    messages = messages_result.scalars().all()

    history = [
        {
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        }
        for msg in reversed(list(messages))
    ]

    return {
        "session_id": session_id,
        "history": history
    }


@router.get("/users/{user_id}/stats", response_model=SessionStatsResponse)
async def get_user_session_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取用户会话统计"""
    total_result = await db.execute(
        select(func.count()).select_from(AISession).where(
            AISession.user_id == user_id,
            AISession.is_deleted == False
        )
    )
    total_sessions = total_result.scalar()

    active_result = await db.execute(
        select(func.count()).select_from(AISession).where(
            AISession.user_id == user_id,
            AISession.is_deleted == False,
            AISession.status == "active"
        )
    )
    active_sessions = active_result.scalar()

    msg_count_result = await db.execute(
        select(func.sum(AISession.total_messages)).where(
            AISession.user_id == user_id,
            AISession.is_deleted == False
        )
    )
    total_messages = msg_count_result.scalar() or 0

    token_count_result = await db.execute(
        select(func.sum(AISession.total_tokens)).where(
            AISession.user_id == user_id,
            AISession.is_deleted == False
        )
    )
    total_tokens = token_count_result.scalar() or 0

    avg_messages = float(total_messages) / total_sessions if total_sessions > 0 else 0.0

    return SessionStatsResponse(
        total_sessions=total_sessions,
        total_messages=total_messages,
        total_tokens=total_tokens,
        active_sessions=active_sessions,
        average_messages_per_session=round(avg_messages, 2)
    )