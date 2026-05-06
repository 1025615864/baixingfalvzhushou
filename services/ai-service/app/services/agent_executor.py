"""Agent执行器 - 纯Agent编排职责"""
import asyncio
import json
import logging
from typing import AsyncIterator, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from app.config.settings import get_settings
from app.services.legal_agent import AgentState, stream_legal_agent
from app.services.llm_client import call_llm_with_fallback, LLMResponse

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    final_response: str
    intent: str
    search_query: str
    retrieved_docs: list[dict]
    iteration_count: int
    latency_ms: int
    sources: list[dict]
    tokens_used: int = 0
    model: str = ""


@dataclass
class StreamEvent:
    event_type: str
    stage: Optional[str] = None
    status: Optional[str] = None
    data: Optional[dict] = None
    token: Optional[str] = None


class AgentExecutor:
    """Agent执行器 - 单一职责：Agent流程编排"""

    def __init__(self):
        self.max_iterations = 3

    async def execute(
        self,
        user_query: str,
        chat_history: list[dict] = None,
        retrieved_docs: list[dict] = None,
        hallucination_feedback: str = "",
        iteration: int = 0
    ) -> AgentResult:
        """执行Agent流程（非流式）"""
        start_time = asyncio.get_event_loop().time()

        initial_state: AgentState = {
            "user_query": user_query,
            "chat_history": chat_history or [],
            "intent": "",
            "search_query": "",
            "retrieved_docs": retrieved_docs or [],
            "draft_response": "",
            "final_response": "",
            "error_flag": False,
            "hallucination_feedback": hallucination_feedback,
            "iteration_count": iteration,
            "stream_mode": False,
            "writer": None
        }

        result = None
        final_response_text = ""
        intent_value = ""
        iteration_value = 0
        done_events = []

        async for event in stream_legal_agent(
            user_query=user_query,
            chat_history=chat_history,
            session_id=None,
            retrieved_docs=retrieved_docs
        ):
            if "stage" in event:
                stage = event.get("stage")
                if stage == "analyzing_intent" and event.get("status") == "completed":
                    intent_value = event.get("intent", "")
                elif stage == "done" and "response" in event:
                    done_events.append(event)

        if done_events:
            last_done = done_events[-1]
            final_response_text = last_done.get("response", "")
            iteration_value = last_done.get("iteration", 0)
        elif not final_response_text:
            final_response_text = "Agent执行超时，请稍后重试。"

        latency_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

        if not final_response_text:
            return AgentResult(
                final_response="Agent执行超时，请稍后重试。",
                intent="",
                search_query="",
                retrieved_docs=[],
                iteration_count=iteration,
                latency_ms=latency_ms,
                sources=[]
            )

        sources = []
        if retrieved_docs:
            for doc in retrieved_docs:
                sources.append({
                    "law_name": doc.get("metadata", {}).get("law_name", ""),
                    "article_num": doc.get("metadata", {}).get("article_num", ""),
                    "text": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", "")
                })

        return AgentResult(
            final_response=final_response_text,
            intent=intent_value,
            search_query="",
            retrieved_docs=retrieved_docs or [],
            iteration_count=iteration_value,
            latency_ms=latency_ms,
            sources=sources,
            tokens_used=0,
            model=settings.llm_model
        )

    async def execute_stream(
        self,
        user_query: str,
        chat_history: list[dict] = None
    ) -> AsyncIterator[StreamEvent]:
        """执行Agent流程（流式）"""
        async for event in stream_legal_agent(
            user_query=user_query,
            chat_history=chat_history,
            session_id=None
        ):
            if "stage" in event:
                yield StreamEvent(
                    event_type="stage",
                    stage=event.get("stage"),
                    status=event.get("status"),
                    data=event
                )
            elif "token" in event:
                yield StreamEvent(
                    event_type="token",
                    token=event.get("token")
                )


_agent_executor: Optional[AgentExecutor] = None


def get_agent_executor() -> AgentExecutor:
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = AgentExecutor()
    return _agent_executor
