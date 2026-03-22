"""法律助手 LangGraph 流式对话路由"""

import json
from typing import Optional, List, AsyncIterator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..agent import get_initial_state
from ..agent.graph_async import compile_async_graph

router = APIRouter()


class LegalChatRequest(BaseModel):
    user_id: int
    message: str
    session_id: Optional[int] = None
    stream: bool = True


class LegalChatResponse(BaseModel):
    session_id: Optional[int] = None
    intent: str
    search_query: Optional[str] = None
    sources: List[dict] = []
    response: str
    error_flag: bool = False


async def run_legal_assistant(user_query: str):
    """
    运行法律助手 LangGraph 工作流

    Args:
        user_query: 用户问题

    Yields:
        JSON 格式的事件流
    """
    graph = compile_async_graph()
    initial_state = get_initial_state(user_query)

    async for event in graph.astream(initial_state):
        for node_name, node_state in event.items():
            if node_name == "intent_analyzer":
                yield json.dumps({
                    "event": "intent",
                    "data": {"intent": node_state.get("intent")}
                }) + "\n"

            elif node_name == "query_rewriter":
                yield json.dumps({
                    "event": "search_query",
                    "data": {"search_query": node_state.get("search_query")}
                }) + "\n"

            elif node_name == "legal_retriever":
                docs = node_state.get("retrieved_docs", [])
                yield json.dumps({
                    "event": "retrieved",
                    "data": {"count": len(docs)}
                }) + "\n"

            elif node_name == "draft_generator":
                draft = node_state.get("draft_response", "")
                yield json.dumps({
                    "event": "draft",
                    "data": {"draft": draft[:100] + "..." if len(draft) > 100 else draft}
                }) + "\n"

            elif node_name == "hallucination_checker":
                if node_state.get("error_flag"):
                    yield json.dumps({
                        "event": "hallucination",
                        "data": {
                            "error_message": node_state.get("error_message"),
                            "retry_count": node_state.get("retry_count")
                        }
                    }) + "\n"

            elif node_name == "casual_chat_handler":
                response = node_state.get("final_response", "")
                yield json.dumps({
                    "event": "response",
                    "data": {"content": response}
                }) + "\n"

            elif node_name == "__end__":
                final = node_state
                yield json.dumps({
                    "event": "done",
                    "data": {
                        "final_response": final.get("final_response", ""),
                        "intent": final.get("intent"),
                        "search_query": final.get("search_query"),
                        "sources": [
                            {
                                "chunk_id": doc.get("chunk_id"),
                                "law_name": doc.get("law_name"),
                                "article_num": doc.get("article_num"),
                                "text": doc.get("text", "")[:100] + "..."
                            }
                            for doc in final.get("retrieved_docs", [])
                        ],
                        "error_flag": final.get("error_flag", False)
                    }
                }) + "\n"


@router.post("/legal/chat", response_model=LegalChatResponse)
async def legal_chat(request: LegalChatRequest):
    """
    非流式法律助手对话

    适用于简单请求-响应模式
    """
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Use /legal/chat/stream for streaming response"
        )

    graph = compile_async_graph()
    initial_state = get_initial_state(request.message)

    result = await graph.ainvoke(initial_state)

    return LegalChatResponse(
        intent=result.get("intent", "unknown"),
        search_query=result.get("search_query"),
        sources=[
            {
                "chunk_id": doc.get("chunk_id"),
                "law_name": doc.get("law_name"),
                "article_num": doc.get("article_num")
            }
            for doc in result.get("retrieved_docs", [])
        ],
        response=result.get("final_response", ""),
        error_flag=result.get("error_flag", False)
    )


@router.post("/legal/chat/stream")
async def legal_chat_stream(request: LegalChatRequest):
    """
    流式法律助手对话

    返回 Server-Sent Events (SSE) 格式的流式响应
    """
    return StreamingResponse(
        run_legal_assistant(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
