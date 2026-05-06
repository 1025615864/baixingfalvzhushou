"""User Service HTTP客户端 - AI会话存储"""
import httpx
from typing import Optional
from .config.settings import get_settings

settings = get_settings()


class UserServiceClient:
    """User Service客户端 - 用于AI会话存储"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.user_service_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def close(self):
        await self.client.close()

    async def create_session(self, user_id: int, title: Optional[str] = None, model: Optional[str] = None) -> dict:
        """创建会话"""
        response = await self.client.post(
            "/api/v1/ai/sessions",
            json={
                "user_id": user_id,
                "title": title,
                "model": model
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_session(self, session_id: str) -> dict:
        """获取会话详情"""
        response = await self.client.get(f"/api/v1/ai/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    async def update_session(self, session_id: str, title: Optional[str] = None, status: Optional[str] = None) -> dict:
        """更新会话"""
        json_data = {}
        if title is not None:
            json_data["title"] = title
        if status is not None:
            json_data["status"] = status
        response = await self.client.put(
            f"/api/v1/ai/sessions/{session_id}",
            json=json_data
        )
        response.raise_for_status()
        return response.json()

    async def delete_session(self, session_id: str) -> dict:
        """删除会话"""
        response = await self.client.delete(f"/api/v1/ai/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    async def list_sessions(self, user_id: int, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> dict:
        """获取用户会话列表"""
        params = {"user_id": user_id, "page": page, "page_size": page_size}
        if status:
            params["status"] = status
        response = await self.client.get("/api/v1/ai/sessions", params=params)
        response.raise_for_status()
        return response.json()

    async def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: Optional[str] = None,
        search_query: Optional[str] = None,
        retrieved_docs: Optional[str] = None,
        draft_response: Optional[str] = None,
        hallucination_feedback: Optional[str] = None,
        tokens: int = 0,
        latency_ms: Optional[int] = None,
        error_flag: bool = False,
        error_message: Optional[str] = None
    ) -> dict:
        """创建消息"""
        response = await self.client.post(
            f"/api/v1/ai/sessions/{session_id}/messages",
            json={
                "role": role,
                "content": content,
                "intent": intent,
                "search_query": search_query,
                "retrieved_docs": retrieved_docs,
                "draft_response": draft_response,
                "hallucination_feedback": hallucination_feedback,
                "tokens": tokens,
                "latency_ms": latency_ms,
                "error_flag": error_flag,
                "error_message": error_message
            }
        )
        response.raise_for_status()
        return response.json()

    async def list_messages(self, session_id: str, page: int = 1, page_size: int = 50) -> dict:
        """获取会话消息列表"""
        response = await self.client.get(
            f"/api/v1/ai/sessions/{session_id}/messages",
            params={"page": page, "page_size": page_size}
        )
        response.raise_for_status()
        return response.json()

    async def get_history(self, session_id: str, limit: int = 10) -> dict:
        """获取会话历史"""
        response = await self.client.get(
            f"/api/v1/ai/sessions/{session_id}/history",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    async def get_user_stats(self, user_id: int) -> dict:
        """获取用户会话统计"""
        response = await self.client.get(f"/api/v1/ai/users/{user_id}/stats")
        response.raise_for_status()
        return response.json()


_user_service_client: Optional[UserServiceClient] = None


def get_user_service_client() -> UserServiceClient:
    global _user_service_client
    if _user_service_client is None:
        _user_service_client = UserServiceClient()
    return _user_service_client


async def close_user_service_client():
    global _user_service_client
    if _user_service_client is not None:
        await _user_service_client.close()
        _user_service_client = None
