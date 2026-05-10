"""AI session management."""
import time
import uuid
from typing import Optional


class SessionManager:
    def __init__(self, max_sessions: int = 100, max_messages_per_session: int = 50):
        self._max_sessions = max_sessions
        self._max_messages_per_session = max_messages_per_session
        self.conversation_histories: dict[str, list[dict]] = {}
        self._last_seen: dict[str, float] = {}

    def get_or_create_session(self, session_id: Optional[str] = None, initial_history: Optional[list[dict]] = None) -> str:
        if session_id is None:
            session_id = uuid.uuid4().hex
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = list(initial_history) if initial_history else []
            self._last_seen[session_id] = time.time()
            self._evict_if_needed()
        else:
            self._last_seen[session_id] = time.time()
        return session_id

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = []
            self._last_seen[session_id] = time.time()
        self.conversation_histories[session_id].append({"role": role, "content": content})
        if len(self.conversation_histories[session_id]) > self._max_messages_per_session:
            self.conversation_histories[session_id] = self.conversation_histories[session_id][-self._max_messages_per_session:]

    def get_history(self, session_id: str) -> list[dict]:
        return self.conversation_histories.get(session_id, [])

    def get_recent_history(self, session_id: str, limit: int = 10) -> list[dict]:
        history = self.conversation_histories.get(session_id, [])
        return history[-limit:]

    def clear_session(self, session_id: str) -> None:
        self.conversation_histories.pop(session_id, None)
        self._last_seen.pop(session_id, None)

    def _evict_if_needed(self) -> None:
        if len(self.conversation_histories) <= self._max_sessions:
            return
        oldest = sorted(self._last_seen.items(), key=lambda x: x[1])
        to_remove = len(self.conversation_histories) - self._max_sessions
        for sid, _ in oldest[:to_remove]:
            self.clear_session(sid)

    def _normalize_history(self, history: list[dict]) -> list[dict]:
        valid_roles = {"user", "assistant"}
        result = []
        for msg in history:
            role = msg.get("role", "").strip().lower()
            content = msg.get("content", "")
            if role in valid_roles and content and content.strip():
                result.append({"role": role, "content": content.strip() if isinstance(content, str) else content})
        if len(result) > self._max_messages_per_session:
            result = result[-self._max_messages_per_session:]
        return result
