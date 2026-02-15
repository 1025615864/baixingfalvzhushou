"""News router module

Modular news routes (2026-01-22)

Contains:
- core: Core news CRUD
- topics: News topics
- subscriptions: News subscriptions
- comments: News comments
- admin: Admin management functions
"""
from .core import router as core_router
from .topics import router as topics_router
from .subscriptions import router as subscriptions_router
from .comments import router as comments_router
from .admin import router as admin_router

from fastapi import APIRouter

router = APIRouter()
router.include_router(admin_router, prefix="/news")
router.include_router(core_router)
router.include_router(topics_router, prefix="/news")
router.include_router(subscriptions_router, prefix="/news")
router.include_router(comments_router, prefix="/news")

__all__ = [
    "router",
    "core_router",
    "topics_router",
    "subscriptions_router",
    "comments_router",
    "admin_router",
]
