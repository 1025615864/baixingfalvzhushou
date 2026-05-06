"""firm routers - 律所领域路由"""
from app.routers.firm import router as firm_router
from app.routers.invitation import router as invitation_router
from app.routers.firm_admin import router as firm_admin_router

__all__ = [
    "firm_router",
    "invitation_router",
    "firm_admin_router",
]