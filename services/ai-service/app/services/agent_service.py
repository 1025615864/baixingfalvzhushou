"""AI Agent服务层 - 整合LegalAgent与远程会话API"""
import json
import time
from typing import Optional, AsyncIterator
from app.config.settings import get_settings
from app.services.legal_agent import legal_agent_graph, AgentState
from app.services.vector_store import search_legal_docs
from app.services.user_service_client import get_user_service_client

settings = get_settings()


class LegalAgentService:
    """法律助手Agent服务 - 支持远程会话存储"""

    def __init__(self):
        self.use_remote = settings.use_remote_session
        self.user_service = None
        if self.use_remote:
            self.user_service = get_user_service_client()

    async def _get_or_create_session(self, user_id: int, message: str, session_id: Optional[str] = None) -> dict:
        """获取或创建会话"""
        if self.use_remote and self.user_service:
            if session_id:
                try:
                    session = await self.user_service.get_session(session_id)
                    return session
                except Exception:
                    pass

            session = await self.user_service.create_session(
                user_id=user_id,
                title=message[:50] if len(message) > 50 else message,
                model=settings.llm_model
            )
            return session
        else:
            return {"id": session_id or "local", "session_id": session_id or "local"}

    async def _save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: str = "",
        search_query: str = "",
        retrieved_docs: list = None,
        tokens: int = 0,
        latency_ms: int = 0,
        error_flag: bool = False,
        error_message: str = ""
    ):
        """保存消息到会话"""
        if self.use_remote and self.user_service:
            try:
                await self.user_service.create_message(
                    session_id=session_id,
                    role=role,
                    content=content,
                    intent=intent,
                    search_query=search_query,
                    retrieved_docs=json.dumps(retrieved_docs, ensure_ascii=False) if retrieved_docs else None,
                    tokens=tokens,
                    latency_ms=latency_ms,
                    error_flag=error_flag,
                    error_message=error_message
                )
            except Exception as e:
                print(f"Failed to save message: {e}")

    async def _get_history(self, session_id: str, limit: int = 10) -> list:
        """获取会话历史"""
        if self.use_remote and self.user_service:
            try:
                result = await self.user_service.get_history(session_id, limit=limit)
                return result.get("history", [])
            except Exception:
                return []
        return []

    async def chat(
        self,
        user_id: int,
        message: str,
        session_id: Optional[str] = None
    ) -> dict:
        """处理用户对话"""
        start_time = time.time()

        session = await self._get_or_create_session(user_id, message, session_id)
        actual_session_id = session.get("session_id", session.get("id", ""))

        history = await self._get_history(actual_session_id, limit=20)
        chat_history = [{"role": h["role"], "content": h["content"]} for h in history]

        initial_state: AgentState = {
            "user_query": message,
            "chat_history": chat_history,
            "intent": "",
            "search_query": "",
            "retrieved_docs": [],
            "draft_response": "",
            "final_response": "",
            "error_flag": False,
            "hallucination_feedback": "",
            "iteration_count": 0
        }

        result = legal_agent_graph.invoke(initial_state)

        latency_ms = int((time.time() - start_time) * 1000)

        sources = []
        for doc in result.get("retrieved_docs", []):
            sources.append({
                "law_name": doc.get("metadata", {}).get("law_name", ""),
                "article_num": doc.get("metadata", {}).get("article_num", ""),
                "text": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", "")
            })

        await self._save_message(
            session_id=actual_session_id,
            role="user",
            content=message,
            intent=result.get("intent", "")
        )

        await self._save_message(
            session_id=actual_session_id,
            role="assistant",
            content=result["final_response"],
            intent=result.get("intent", ""),
            search_query=result.get("search_query", ""),
            retrieved_docs=result.get("retrieved_docs", []),
            tokens=len(result["final_response"]) // 4,
            latency_ms=latency_ms,
            error_flag=result.get("error_flag", False)
        )

        return {
            "session_id": actual_session_id,
            "message": result["final_response"],
            "model": settings.llm_model,
            "sources": sources
        }

    async def get_sessions(self, user_id: int) -> list[dict]:
        """获取用户会话列表"""
        if self.use_remote and self.user_service:
            try:
                result = await self.user_service.list_sessions(user_id=user_id)
                return result.get("sessions", [])
            except Exception:
                return []
        return []

    async def get_history(self, session_id: str) -> list[dict]:
        """获取会话历史"""
        if self.use_remote and self.user_service:
            try:
                result = await self.user_service.list_messages(session_id=session_id)
                return [
                    {
                        "role": m["role"],
                        "content": m["content"],
                        "created_at": m.get("created_at", ""),
                        "metadata": {}
                    }
                    for m in result.get("messages", [])
                ]
            except Exception:
                return []
        return []


class StreamingLegalAgentService(LegalAgentService):
    """支持流式输出的法律助手服务"""

    async def chat_stream(
        self,
        user_id: int,
        message: str,
        session_id: Optional[str] = None
    ) -> AsyncIterator[dict]:
        """流式处理对话 - 返回SSE事件迭代器"""
        start_time = time.time()

        session = await self._get_or_create_session(user_id, message, session_id)
        actual_session_id = session.get("session_id", session.get("id", ""))

        history = await self._get_history(actual_session_id, limit=20)
        chat_history = [{"role": h["role"], "content": h["content"]} for h in history]

        initial_state: AgentState = {
            "user_query": message,
            "chat_history": chat_history,
            "intent": "",
            "search_query": "",
            "retrieved_docs": [],
            "draft_response": "",
            "final_response": "",
            "error_flag": False,
            "hallucination_feedback": "",
            "iteration_count": 0
        }

        collected_response = ""
        retrieved_docs = []

        async for event in legal_agent_graph.astream(initial_state):
            for node_name, node_data in event.items():
                if node_name == "Hallucination_Checker":
                    continue
                if isinstance(node_data, dict):
                    if "final_response" in node_data:
                        new_content = node_data["final_response"]
                        if new_content and new_content != collected_response:
                            delta = new_content[len(collected_response):]
                            collected_response = new_content
                            yield {
                                "event": "message",
                                "data": delta
                            }
                    if "retrieved_docs" in node_data:
                        retrieved_docs = node_data["retrieved_docs"]

        latency_ms = int((time.time() - start_time) * 1000)

        yield {
            "event": "done",
            "data": {
                "session_id": actual_session_id,
                "sources": [
                    {
                        "law_name": doc.get("metadata", {}).get("law_name", ""),
                        "article_num": doc.get("metadata", {}).get("article_num", ""),
                        "text": doc.get("content", "")[:200] if doc.get("content") else ""
                    }
                    for doc in retrieved_docs
                ]
            }
        }

        await self._save_message(
            session_id=actual_session_id,
            role="user",
            content=message
        )

        await self._save_message(
            session_id=actual_session_id,
            role="assistant",
            content=collected_response,
            retrieved_docs=retrieved_docs,
            tokens=len(collected_response) // 4,
            latency_ms=latency_ms
        )
