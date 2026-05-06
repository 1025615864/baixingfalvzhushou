"""消息持久化器 - 纯消息存储职责"""
import json
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MessageRecord:
    role: str
    content: str
    intent: str = ""
    search_query: str = ""
    retrieved_docs: list = None
    draft_response: str = ""
    hallucination_feedback: str = ""
    tokens: int = 0
    latency_ms: int = 0
    error_flag: bool = False
    error_message: str = ""


class MessagePersistence:
    """消息持久化器 - 单一职责：消息存储"""

    def __init__(self, user_service_client=None):
        self._client = user_service_client

    async def save_user_message(
        self,
        session_id: str,
        content: str,
        intent: str = "",
        search_query: str = "",
        error_flag: bool = False,
        error_message: str = ""
    ) -> bool:
        """保存用户消息"""
        if not self._client:
            logger.debug(f"[Local] User message saved: {content[:50]}...")
            return True

        try:
            await self._client.create_message(
                session_id=session_id,
                role="user",
                content=content,
                intent=intent,
                search_query=search_query,
                error_flag=error_flag,
                error_message=error_message
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")
            return False

    async def save_assistant_message(
        self,
        session_id: str,
        content: str,
        intent: str = "",
        search_query: str = "",
        retrieved_docs: list = None,
        hallucination_feedback: str = "",
        tokens: int = 0,
        latency_ms: int = 0,
        error_flag: bool = False,
        error_message: str = ""
    ) -> bool:
        """保存助手消息"""
        if not self._client:
            logger.debug(f"[Local] Assistant message saved: {content[:50]}...")
            return True

        try:
            await self._client.create_message(
                session_id=session_id,
                role="assistant",
                content=content,
                intent=intent,
                search_query=search_query,
                retrieved_docs=json.dumps(retrieved_docs, ensure_ascii=False) if retrieved_docs else None,
                hallucination_feedback=hallucination_feedback,
                tokens=tokens,
                latency_ms=latency_ms,
                error_flag=error_flag,
                error_message=error_message
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save assistant message: {e}")
            return False

    async def save_message(self, session_id: str, message: MessageRecord) -> bool:
        """统一保存消息"""
        if message.role == "user":
            return await self.save_user_message(
                session_id=session_id,
                content=message.content,
                intent=message.intent,
                search_query=message.search_query,
                error_flag=message.error_flag,
                error_message=message.error_message
            )
        else:
            return await self.save_assistant_message(
                session_id=session_id,
                content=message.content,
                intent=message.intent,
                search_query=message.search_query,
                retrieved_docs=message.retrieved_docs,
                hallucination_feedback=message.hallucination_feedback,
                tokens=message.tokens,
                latency_ms=message.latency_ms,
                error_flag=message.error_flag,
                error_message=message.error_message
            )


_message_persistence: Optional[MessagePersistence] = None


def get_message_persistence(user_service_client=None) -> MessagePersistence:
    global _message_persistence
    if _message_persistence is None:
        _message_persistence = MessagePersistence(user_service_client)
    return _message_persistence
