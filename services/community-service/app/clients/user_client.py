"""服务间通信客户端"""
import os
import logging
from typing import Optional, Any
import httpx

logger = logging.getLogger(__name__)


class ServiceClient:
    def __init__(self, service_name: str, base_url: str, timeout: float = 30.0):
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, path: str, **kwargs) -> httpx.Response:
        client = await self._get_client()
        return await client.get(path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        client = await self._get_client()
        return await client.post(path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        client = await self._get_client()
        return await client.put(path, **kwargs)

    async def patch(self, path: str, **kwargs) -> httpx.Response:
        client = await self._get_client()
        return await client.patch(path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        client = await self._get_client()
        return await client.delete(path, **kwargs)


class UserServiceClient(ServiceClient):
    def __init__(self):
        base_url = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
        super().__init__("user-service", base_url)

    async def get_user_info(self, user_id: int) -> Optional[dict[str, Any]]:
        try:
            response = await self.get(f"/api/v1/users/{user_id}")
            if response.status_code == 200:
                data = response.json()
                return {
                    "user_id": data.get("id"),
                    "nickname": data.get("nickname"),
                    "avatar": data.get("avatar"),
                    "role": data.get("role", "user"),
                    "is_lawyer": data.get("role") == "lawyer"
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None

    async def verify_token(self, token: str) -> Optional[dict[str, Any]]:
        try:
            response = await self.post(
                "/api/v1/auth/validate",
                json={"token": token}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to verify token: {e}")
            return None

    async def get_user_permissions(self, user_id: int) -> Optional[dict[str, Any]]:
        try:
            response = await self.get(f"/api/v1/users/{user_id}/permissions")
            if response.status_code == 200:
                return response.json()
            return {"roles": [], "permissions": []}
        except Exception as e:
            logger.error(f"Failed to get permissions for user {user_id}: {e}")
            return {"roles": [], "permissions": []}


user_service_client = UserServiceClient()
