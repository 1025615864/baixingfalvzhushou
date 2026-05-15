"""Order service routers package"""
from .orders import router
from .admin import admin_router
from .agent import router as agent_router

__all__ = ["router", "admin_router", "agent_router"]
