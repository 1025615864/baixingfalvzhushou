"""AI对话路由 - 基于ChatOrchestrator"""
import json
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.chat_orchestrator import ChatOrchestrator, ChatRequest, ChatResponse, get_chat_orchestrator
from app.services.input_sanitizer import sanitize_user_input, InputSanitizer
from app.dependencies.auth import get_current_user, UserContext

router = APIRouter()
logger = logging.getLogger(__name__)
input_sanitizer = InputSanitizer()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: UserContext = Depends(get_current_user)):
    """AI对话（非流式）- 支持匿名用户"""
    sanitize_result = sanitize_user_input(request.message)
    if not sanitize_result.success:
        raise HTTPException(status_code=400, detail=sanitize_result.blocked_reason)

    try:
        if user.user_id == 0 and not request.session_id:
            request.user_id = 0
        else:
            request.user_id = user.user_id

        orchestrator = get_chat_orchestrator()
        result = await orchestrator.chat(request)
        return ChatResponse(
            session_id=result.session_id,
            message=result.message,
            model=result.model,
            sources=result.sources,
            intent=result.intent,
            latency_ms=result.latency_ms
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/rag")
async def debug_rag(query: str = "老板不发工资怎么办"):
    """调试RAG检索"""
    try:
        from app.services.rag_retrieval import retrieve_with_fallback
        result = await retrieve_with_fallback(query=query, intent="legal", top_k=3)
        return {
            "query": query,
            "retrieval_level": result.retrieval_level,
            "total_count": result.total_count,
            "sufficient": result.sufficient,
            "docs": [{"id": d.id, "content": d.content[:100], "similarity": d.similarity} for d in result.docs]
        }
    except Exception as e:
        logger.error(f"RAG debug error: {e}")
        return {"error": str(e)}


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, user: UserContext = Depends(get_current_user)):
    """AI对话（流式SSE）- 支持匿名用户"""
    sanitize_result = sanitize_user_input(request.message)
    if not sanitize_result.success:
        yield f"data: {json.dumps({'type': 'error', 'error': sanitize_result.blocked_reason})}\n\n"
        return

    if user.user_id == 0 and not request.session_id:
        request.user_id = 0
    else:
        request.user_id = user.user_id

    async def event_generator():
        try:
            orchestrator = get_chat_orchestrator()

            async for event in orchestrator.chat_stream(request):
                if event.get("event") == "session":
                    yield f"data: {json.dumps({'type': 'session', 'session_id': event.get('session_id')})}\n\n"
                elif event.get("event") == "stage":
                    yield f"data: {json.dumps({'type': 'stage', **event})}\n\n"
                elif event.get("event") == "token":
                    yield f"data: {json.dumps({'type': 'token', 'content': event.get('content', '')})}\n\n"
                elif event.get("event") == "done":
                    yield f"data: {json.dumps({'type': 'done', 'session_id': event.get('session_id')})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/sessions/{user_id}")
async def get_sessions(user_id: int):
    """获取用户会话列表"""
    try:
        orchestrator = get_chat_orchestrator()
        sessions = await orchestrator.get_sessions(user_id)
        return {"items": sessions}
    except Exception as e:
        logger.error(f"Get sessions error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str, user: UserContext = Depends(get_current_user)):
    """获取会话历史 - 支持匿名用户"""
    try:
        orchestrator = get_chat_orchestrator()
        messages = await orchestrator.get_history(session_id)
        return {"items": messages}
    except Exception as e:
        logger.error(f"Get history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
