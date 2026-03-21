"""AI对话路由"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services.legal_agent import LegalAgentService

router = APIRouter()


class ChatRequest(BaseModel):
    user_id: int
    message: str
    session_id: Optional[int] = None


class ChatResponse(BaseModel):
    session_id: int
    message: str
    model: str
    sources: List[dict] = []


class SessionResponse(BaseModel):
    id: int
    user_id: int
    session_type: str
    title: Optional[str] = None
    status: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """AI对话"""
    agent_service = LegalAgentService(db)
    result = await agent_service.chat(
        user_id=request.user_id,
        message=request.message,
        session_id=request.session_id,
    )
    return ChatResponse(**result)


@router.get("/sessions/{user_id}")
async def get_sessions(
    user_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取用户会话列表"""
    agent_service = LegalAgentService(db)
    sessions = await agent_service.get_sessions(user_id)
    return {"items": sessions}


@router.get("/sessions/{session_id}/history")
async def get_history(
    session_id: int,
    db: AsyncSession = Depends(lambda: AsyncSessionLocal())
):
    """获取会话历史"""
    agent_service = LegalAgentService(db)
    messages = await agent_service.get_history(session_id)
    return {"items": messages}
