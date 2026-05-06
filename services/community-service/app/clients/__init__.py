"""社区服务客户端"""
from .user_client import UserServiceClient, user_service_client
from .ai_client import AIClient, ai_client

__all__ = ["UserServiceClient", "user_service_client", "AIClient", "ai_client"]
