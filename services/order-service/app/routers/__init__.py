"""Order service routers package"""
from .orders import router
from .admin import admin_router

__all__ = ["router", "admin_router"]
