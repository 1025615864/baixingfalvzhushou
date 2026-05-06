"""AI服务路由"""
from .chat import router as chat_router
from .agent import router as agent_router
from .config import router as config_router
from .metrics import router as metrics_router
from .websocket import router as websocket_router
from .health import router as health_router
from .ai_ops import router as ai_ops_router

__all__ = [
    "chat_router",
    "agent_router",
    "config_router",
    "metrics_router",
    "websocket_router",
    "health_router",
    "ai_ops_router",
]
