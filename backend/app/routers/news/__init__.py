from fastapi import APIRouter

router = APIRouter(prefix="/news", tags=["News"])

try:
    from .core import router as core_router
    router.include_router(core_router)
except ImportError:
    pass

__all__ = ["router"]
