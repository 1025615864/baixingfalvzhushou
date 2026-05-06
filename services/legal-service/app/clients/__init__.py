"""clients package"""
from .user_client import user_service_client
from .ai_client import ai_service_client

__all__ = ["user_service_client", "ai_service_client"]