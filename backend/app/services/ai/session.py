"""会话管理"""
import time
import uuid


class SessionManager:
    """会话管理器"""

    def __init__(
        self,
        max_sessions: int = 5000,
        max_messages_per_session: int = 50,
    ):
        self.conversation_histories: dict[str, list[dict[str, str]]] = {}
        self._last_seen: dict[str, float] = {}
        self._max_sessions = max_sessions
        self._max_messages_per_session = max_messages_per_session

    def get_or_create_session(
        self,
        session_id: str | None = None,
        *,
        initial_history: list[dict[str, str]] | None = None,
    ) -> str:
        if session_id and session_id in self.conversation_histories:
            self._last_seen[session_id] = time.time()
            return session_id

        new_session_id = session_id or uuid.uuid4().hex
        if new_session_id not in self.conversation_histories:
            self.conversation_histories[new_session_id] = []

        existing = self.conversation_histories.get(new_session_id, [])
        if (not existing) and initial_history:
            self.conversation_histories[new_session_id] = self._normalize_history(
                initial_history)

        self._last_seen[new_session_id] = time.time()
        self._evict_if_needed()
        return new_session_id

    def clear_session(self, session_id: str) -> None:
        _ = self.conversation_histories.pop(str(session_id), None)
        _ = self._last_seen.pop(str(session_id), None)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self.conversation_histories:
            self.conversation_histories[session_id] = []

        history = self.conversation_histories[session_id]
        history.append({"role": role, "content": content})
        self.conversation_histories[session_id] = history[-self._max_messages_per_session:]
        self._last_seen[session_id] = time.time()
        self._evict_if_needed()

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        return self.conversation_histories.get(session_id, [])

    def get_recent_history(self, session_id: str,
                           limit: int = 10) -> list[dict[str, str]]:
        history = self.conversation_histories.get(session_id, [])
        return history[-limit:]

    def _normalize_history(
            self, history: list[dict[str, str]]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for item in history:
            role = str(item.get("role", "")).strip().lower()
            if role not in {"user", "assistant"}:
                continue
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            normalized.append({"role": role, "content": content})

        if not normalized:
            return []
        return normalized[-self._max_messages_per_session:]

    def _evict_if_needed(self) -> None:
        if len(self.conversation_histories) <= self._max_sessions:
            return

        oldest_session: str | None = None
        oldest_time = float("inf")
        for sid, ts in self._last_seen.items():
            if ts < oldest_time:
                oldest_time = ts
                oldest_session = sid

        if oldest_session is not None:
            _ = self.conversation_histories.pop(oldest_session, None)
            _ = self._last_seen.pop(oldest_session, None)
