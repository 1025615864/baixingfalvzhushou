"""用户服务客户端 - 调用 User Service API"""
import os
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class UserServiceClient:
    """用户服务 HTTP 客户端"""

    def __init__(self):
        self.user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
        self.api_base = f"{self.user_service_url}/api/v1"
        self._client: Optional[httpx.AsyncClient] = None
        self._enabled = os.getenv("USER_SERVICE_ENABLED", "false").lower() in {"1", "true", "yes"}

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证用户 Token（如果 User Service 提供此接口）"""
        if not self._enabled:
            return None

        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.api_base}/auth/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户画像"""
        if not self._enabled:
            return None

        try:
            client = await self._get_client()
            response = await client.get(f"{self.api_base}/profiles/{user_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.warning(f"Failed to get user profile: {e}")
            return None

    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户基本信息"""
        if not self._enabled:
            return None

        try:
            client = await self._get_client()
            response = await client.get(f"{self.api_base}/users/{user_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.warning(f"Failed to get user info: {e}")
            return None

    async def check_user_membership(self, user_id: int) -> Optional[str]:
        """检查用户会员等级"""
        if not self._enabled:
            return "free"

        try:
            client = await self._get_client()
            response = await client.get(f"{self.api_base}/memberships/{user_id}")
            if response.status_code == 200:
                data = response.json()
                return data.get("level", "free")
            return "free"
        except Exception as e:
            logger.warning(f"Failed to check membership: {e}")
            return "free"

    async def notify_user(self, user_id: int, notification: Dict[str, Any]) -> bool:
        """通知用户（如果 User Service 提供此接口）"""
        if not self._enabled:
            return False

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.api_base}/notifications/",
                json={"user_id": user_id, **notification}
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.warning(f"Failed to notify user: {e}")
            return False

    async def get_consultation_quota(self, user_id: int) -> Dict[str, int]:
        """获取用户咨询配额"""
        membership = await self.check_user_membership(user_id)

        quotas = {
            "free": {"daily": 2, "monthly": 5},
            "basic": {"daily": 5, "monthly": 20},
            "premium": {"daily": 20, "monthly": 100},
            "enterprise": {"daily": 100, "monthly": 1000},
        }

        return quotas.get(membership, quotas["free"])

    async def record_user_action(
        self,
        user_id: int,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """记录用户行为（用于分析）"""
        if not self._enabled:
            return False

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.api_base}/analytics/actions/",
                json={
                    "user_id": user_id,
                    "action": action,
                    "details": details or {},
                }
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.warning(f"Failed to record user action: {e}")
            return False


user_service_client = UserServiceClient()