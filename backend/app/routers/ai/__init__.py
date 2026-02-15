"""AI router module

Modular AI routes (2026-01-22)

Contains:
- chat: AI chat endpoints
- consultations: AI consultation management
- share: Share functionality
- transcription: Speech-to-text
- analysis: File analysis

Migrated to ai/ submodules
"""
from .chat import settings
from . import chat
from .chat import router as chat_router
from .consultations import router as consultations_router
from .share import router as share_router
from .transcription import router as transcription_router
from .analysis import router as analysis_router

# Re-export report generator functions for testing
from ...services.report_generator import (
    generate_consultation_report_pdf,
    build_consultation_report_from_export_data,
)

# Aggregate all routers into one for backwards compatibility
from fastapi import APIRouter

router = APIRouter()
router.include_router(chat_router)
router.include_router(consultations_router)
router.include_router(share_router)
router.include_router(transcription_router)
router.include_router(analysis_router)

# Export settings and functions for testing

# Re-export _try_get_ai_assistant from chat module
# Note: monkeypatch.setattr(ai_router, "_try_get_ai_assistant", ...) won't affect chat._try_get_ai_assistant
# Tests should mock app.routers.ai.chat._try_get_ai_assistant instead
_try_get_ai_assistant = chat._try_get_ai_assistant

__all__ = [
    "router",
    "chat_router",
    "consultations_router",
    "share_router",
    "transcription_router",
    "analysis_router",
    "generate_consultation_report_pdf",
    "build_consultation_report_from_export_data",
    "settings",
]
