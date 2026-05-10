from fastapi import APIRouter

router = APIRouter(prefix="/forum", tags=["Forum"])

try:
    from .comments import router as comments_router
    router.include_router(comments_router)
except ImportError:
    pass

try:
    from .favorites import router as favorites_router
    router.include_router(favorites_router)
except ImportError:
    pass

try:
    from .reactions import router as reactions_router
    router.include_router(reactions_router)
except ImportError:
    pass

__all__ = ["router"]
