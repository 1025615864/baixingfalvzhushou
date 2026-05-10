from fastapi import APIRouter
from app.config.settings import settings

router = APIRouter(prefix="/ai", tags=["AI"])

try:
    from .chat import router as chat_router
    router.include_router(chat_router)
except ImportError:
    pass

try:
    from .analysis import router as analysis_router
    router.include_router(analysis_router)
except ImportError:
    pass

try:
    from .transcription import router as transcription_router
    router.include_router(transcription_router)
except ImportError:
    pass

__all__ = ["router", "settings"]
