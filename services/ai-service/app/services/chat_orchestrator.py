"""聊天编排器 - 统一编排层"""
import json
import logging
import time
from typing import AsyncIterator, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime

from app.config.settings import get_settings
from app.services.session_manager import SessionManager, ChatMessage, get_session_manager
from app.services.agent_executor import AgentExecutor, StreamEvent, get_agent_executor
from app.services.message_persistence import MessagePersistence, MessageRecord, get_message_persistence
from app.services.rag_retrieval import retrieve_with_fallback
from app.services.quality_service import get_quality_service

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class ChatRequest:
    user_id: int
    message: str
    session_id: Optional[str] = None


@dataclass
class ChatResponse:
    session_id: str
    message: str
    model: str
    sources: List[dict]
    intent: str
    latency_ms: int


class ChatOrchestrator:
    """聊天编排器 - 统一编排各个组件"""

    def __init__(
        self,
        session_manager: SessionManager = None,
        agent_executor: AgentExecutor = None,
        message_persistence: MessagePersistence = None
    ):
        self.session_manager = session_manager or get_session_manager()
        self.agent_executor = agent_executor or get_agent_executor()
        self.message_persistence = message_persistence or get_message_persistence()

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """处理非流式对话"""
        start_time = time.time()

        session = await self.session_manager.get_or_create_session(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id
        )
        session_id = session.session_id

        history = await self.session_manager.get_history(session_id, limit=20)
        chat_history = [{"role": h.role, "content": h.content} for h in history]

        retrieved_result = await retrieve_with_fallback(
            query=request.message,
            intent="legal",
            top_k=5
        )

        retrieved_docs = [
            {
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata,
                "distance": 1.0 - doc.similarity
            }
            for doc in retrieved_result.docs
        ]

        await self.message_persistence.save_user_message(
            session_id=session_id,
            content=request.message,
            intent="legal"
        )

        agent_result = await self.agent_executor.execute(
            user_query=request.message,
            chat_history=chat_history,
            retrieved_docs=retrieved_docs
        )

        await self.message_persistence.save_assistant_message(
            session_id=session_id,
            content=agent_result.final_response,
            intent=agent_result.intent,
            search_query=agent_result.search_query,
            retrieved_docs=agent_result.retrieved_docs,
            hallucination_feedback="",
            tokens=len(agent_result.final_response) // 4,
            latency_ms=agent_result.latency_ms
        )

        total_latency_ms = int((time.time() - start_time) * 1000)

        try:
            quality_svc = get_quality_service()
            await quality_svc.record_token_usage(
                conversation_id=session_id,
                model_name=agent_result.model or settings.llm_model,
                prompt_tokens=0,
                completion_tokens=len(agent_result.final_response) // 4,
                latency_ms=total_latency_ms
            )
        except Exception as e:
            logger.warning(f"Failed to record token usage: {e}")

        return ChatResponse(
            session_id=session_id,
            message=agent_result.final_response,
            model=settings.llm_model,
            sources=agent_result.sources,
            intent=agent_result.intent,
            latency_ms=total_latency_ms
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[dict]:
        """处理流式对话"""
        start_time = time.time()

        session = await self.session_manager.get_or_create_session(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id
        )
        session_id = session.session_id

        history = await self.session_manager.get_history(session_id, limit=20)
        chat_history = [{"role": h.role, "content": h.content} for h in history]

        yield {
            "event": "session",
            "session_id": session_id
        }

        collected_response = ""
        retrieved_docs = []

        async for event in self.agent_executor.execute_stream(
            user_query=request.message,
            chat_history=chat_history
        ):
            if event.event_type == "stage":
                yield {
                    "event": "stage",
                    "stage": event.stage,
                    "status": event.status,
                    "data": event.data
                }

                if event.stage == "retrieving_knowledge" and event.data:
                    if "count" in event.data:
                        retrieved_docs = []

                if event.stage == "done" and event.data:
                    if "response" in event.data:
                        collected_response = event.data["response"]

            elif event.event_type == "token":
                collected_response += event.token or ""
                yield {
                    "event": "token",
                    "content": event.token
                }

        latency_ms = int((time.time() - start_time) * 1000)

        yield {
            "event": "done",
            "session_id": session_id,
            "sources": retrieved_docs,
            "latency_ms": latency_ms
        }

        await self.message_persistence.save_user_message(
            session_id=session_id,
            content=request.message
        )

        await self.message_persistence.save_assistant_message(
            session_id=session_id,
            content=collected_response,
            tokens=len(collected_response) // 4,
            latency_ms=latency_ms,
            retrieved_docs=retrieved_docs
        )

    async def get_sessions(self, user_id: int) -> List[dict]:
        """获取用户会话列表"""
        result = await self.session_manager.list_sessions(user_id)
        return result.get("sessions", [])

    async def get_history(self, session_id: str) -> List[dict]:
        """获取会话历史"""
        history = await self.session_manager.get_history(session_id)
        return [
            {
                "role": h.role,
                "content": h.content,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in history
        ]


_orchestrator: Optional[ChatOrchestrator] = None


def get_chat_orchestrator(
    session_manager: SessionManager = None,
    agent_executor: AgentExecutor = None,
    message_persistence: MessagePersistence = None
) -> ChatOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ChatOrchestrator(
            session_manager=session_manager,
            agent_executor=agent_executor,
            message_persistence=message_persistence
        )
    return _orchestrator


SessionManager.get_or_create_session = lambda self, user_id, message, session_id=None: (
    self.create_session(user_id, message) if not session_id else
    (self.get_session(session_id) or self.create_session(user_id, message))
)
