"""用户服务层 - BFF 代理

⚠️ 已迁移到 services/user-service/
⚠️ 本文件仅作为 BFF 代理层，转发请求到微服务

Backend 不再直接操作数据库，而是通过 HTTP/gRPC 调用 user-service。
"""
import os
import httpx
from typing import Optional


USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")


class UserServiceProxy:
    """用户服务代理 - 转发请求到 user-service 微服务"""

    @staticmethod
    async def create_user(user_data: dict) -> dict:
        """创建用户 - 转发到 user-service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{USER_SERVICE_URL}/api/v1/users",
                json=user_data,
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_user(user_id: int) -> Optional[dict]:
        """获取用户 - 转发到 user-service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/api/v1/users/{user_id}",
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def authenticate(username: str, password: str) -> Optional[dict]:
        """认证用户 - 转发到 user-service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{USER_SERVICE_URL}/api/v1/auth/login",
                json={"username": username, "password": password},
            )
            if response.status_code == 401:
                return None
            response.raise_for_status()
            return response.json()


user_service = UserServiceProxy()
