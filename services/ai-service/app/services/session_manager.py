"""会话管理器 - 纯会话管理职责"""
import logging
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
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


@dataclass
class ChatMessage:
    role: str
    content: str
    created_at: Optional[datetime] = None
    intent: Optional[str] = None
    metadata: Optional[dict] = None


class SessionManager:
    """会话管理器 - 单一职责：会话生命周期管理"""

    def __init__(self, user_service_client=None):
        self._client = user_service_client

    async def create_session(
        self,
        user_id: int,
        message: str,
        model: Optional[str] = None
    ) -> SessionInfo:
        """创建新会话"""
        if self._client:
            try:
                session = await self._client.create_session(
                    user_id=user_id,
                    title=message[:50] if len(message) > 50 else message,
                    model=model
                )
                return SessionInfo(
                    session_id=session.get("session_id", ""),
                    user_id=session.get("user_id", user_id),
                    title=session.get("title"),
                    status=session.get("status", "active"),
                    total_messages=0,
                    total_tokens=0,
                    model=session.get("model"),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    last_message_at=None
                )
            except Exception as e:
                logger.error(f"Failed to create remote session: {e}")

        return SessionInfo(
            session_id=f"local_{user_id}_{int(datetime.now().timestamp())}",
            user_id=user_id,
            title=message[:50] if len(message) > 50 else message,
            status="active",
            total_messages=0,
            total_tokens=0,
            model=model,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_message_at=None
        )

    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """获取会话信息"""
        if self._client:
            try:
                session = await self._client.get_session(session_id)
                return SessionInfo(
                    session_id=session.get("session_id", session_id),
                    user_id=session.get("user_id", 0),
                    title=session.get("title"),
                    status=session.get("status", "active"),
                    total_messages=session.get("total_messages", 0),
                    total_tokens=session.get("total_tokens", 0),
                    model=session.get("model"),
                    created_at=datetime.fromisoformat(session.get("created_at", datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(session.get("updated_at", datetime.now().isoformat())),
                    last_message_at=datetime.fromisoformat(session["last_message_at"]) if session.get("last_message_at") else None
                )
            except Exception as e:
                logger.error(f"Failed to get remote session: {e}")
        return None

    async def get_history(self, session_id: str, limit: int = 20) -> List[ChatMessage]:
        """获取会话历史"""
        if self._client:
            try:
                result = await self._client.get_history(session_id, limit=limit)
                history = result.get("history", [])
                return [
                    ChatMessage(
                        role=h.get("role", "user"),
                        content=h.get("content", ""),
                        created_at=datetime.fromisoformat(h["created_at"]) if h.get("created_at") else None
                    )
                    for h in history
                ]
            except Exception as e:
                logger.error(f"Failed to get remote history: {e}")

        return []

    async def list_sessions(self, user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取用户会话列表"""
        if self._client:
            try:
                return await self._client.list_sessions(user_id, page, page_size)
            except Exception as e:
                logger.error(f"Failed to list remote sessions: {e}")

        return {"sessions": [], "total": 0, "page": page, "page_size": page_size}

    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if self._client:
            try:
                await self._client.delete_session(session_id)
                return True
            except Exception as e:
                logger.error(f"Failed to delete remote session: {e}")
        return False

    async def get_or_create_session(
        self,
        user_id: int,
        message: str,
        session_id: Optional[str] = None
    ) -> "SessionInfo":
        """获取或创建会话"""
        if session_id:
            existing = await self.get_session(session_id)
            if existing:
                return existing

        return await self.create_session(user_id, message)


_session_manager: Optional[SessionManager] = None


def get_session_manager(user_service_client=None) -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(user_service_client)
    return _session_manager
