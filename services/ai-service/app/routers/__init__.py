"""AI服务路由"""
from .chat import router as chat_router
from .agent import router as agent_router
from .config import router as config_router
from .legal_chat import router as legal_chat_router

__all__ = ["chat_router", "agent_router", "config_router", "legal_chat_router"]
