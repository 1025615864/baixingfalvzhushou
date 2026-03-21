"""法律服务路由"""
from .consultation import router as consultation_router
from .lawyer import router as lawyer_router
from .firm import router as firm_router

__all__ = ["consultation_router", "lawyer_router", "firm_router"]
