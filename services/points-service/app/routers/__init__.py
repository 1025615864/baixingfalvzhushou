"""积分服务路由"""
from .points import router as points_router
from .agent import router as agent_router

__all__ = ["points_router", "agent_router"]
