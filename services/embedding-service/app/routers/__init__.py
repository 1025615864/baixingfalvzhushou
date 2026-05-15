from .embedding import router as embedding_router
from .admin import router as admin_router
from .agent import router as agent_router

__all__ = ["embedding_router", "admin_router", "agent_router"]
