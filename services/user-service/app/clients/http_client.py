"""服务间HTTP通信客户端"""
import logging
from typing import Optional, Any
import httpx

from ..config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ServiceClient:
    """服务通信基类"""

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
    """用户服务客户端 - 供其他服务调用"""

    def __init__(self):
        base_url = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
        super().__init__("user-service", base_url)

    async def get_user_by_id(self, user_id: int) -> Optional[dict[str, Any]]:
        """获取用户信息"""
        try:
            response = await self.get(f"/api/v1/users/{user_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None

    async def get_user_by_username(self, username: str) -> Optional[dict[str, Any]]:
        """通过用户名获取用户"""
        try:
            response = await self.get(f"/api/v1/users/username/{username}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None

    async def validate_token(self, token: str) -> Optional[dict[str, Any]]:
        """验证Token"""
        try:
            response = await self.post(
                "/api/v1/auth/validate",
                json={"token": token}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to validate token: {e}")
            return None

    async def verify_permissions(self, user_id: int, required_role: str) -> bool:
        """验证用户权限"""
        try:
            response = await self.get(
                f"/api/v1/users/{user_id}/role",
                params={"required": required_role}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to verify permissions for user {user_id}: {e}")
            return False


class BackendClient(ServiceClient):
    """后端服务客户端 - user-service调用后端"""

    def __init__(self):
        base_url = os.getenv("BACKEND_URL", "http://localhost:8080")
        super().__init__("backend", base_url)

    async def get_lawyer_info(self, user_id: int) -> Optional[dict[str, Any]]:
        """获取律师信息"""
        try:
            response = await self.get(f"/api/v1/lawyers/user/{user_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to get lawyer info: {e}")
            return None

    async def get_membership_info(self, user_id: int) -> Optional[dict[str, Any]]:
        """获取会员信息"""
        try:
            response = await self.get(f"/api/v1/membership/{user_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to get membership info: {e}")
            return None


import os
user_service_client = UserServiceClient()
backend_client = BackendClient()
