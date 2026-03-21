"""API路由"""

import logging

from .settlement import router as settlement_router
from fastapi import APIRouter

logger = logging.getLogger(__name__)

from . import admin_v1

from . import (
    analytics,
    calendar,
    channel_tracking,
    cross_domain,
    document,
    home,
    knowledge,
    lawfirm,
    upload,
    feedback,
    reviews,
    faq,
    admin_monitor,
    vertical_channel,
    integration,
    moderation,
    knowledge_admin,
    promotion,
    enterprise,
    wechat,
    wechat_pay,
    membership,
    security,
    ab_testing,
    funnel_analysis,
    video_consultation)

from . import admin

try:
    from . import system
except Exception:
    logger.exception("Failed to import system router")
    system = None

api_router = APIRouter()
legacy_api_router = APIRouter()

api_router.include_router(admin_v1.router)

if system is not None:
    system_router = getattr(system, "router", None)
    if system_router is not None:
        api_router.include_router(system_router)

api_router.include_router(lawfirm.router)
api_router.include_router(admin.router)
api_router.include_router(upload.router)
api_router.include_router(knowledge.router)

api_router.include_router(document.router)
api_router.include_router(calendar.router)
api_router.include_router(feedback.router)

api_router.include_router(settlement_router)
api_router.include_router(reviews.router)
api_router.include_router(analytics.router)
api_router.include_router(faq.router)
api_router.include_router(admin_monitor.router)

try:
    from . import system_admin
except Exception:
    logger.exception("Failed to import system_admin router")
    system_admin = None

if system_admin is not None:
    system_admin_router = getattr(system_admin, "router", None)
    if system_admin_router is not None:
        api_router.include_router(system_admin_router)

__all__ = ["api_router", "legacy_api_router"]

api_router.include_router(vertical_channel.router)
api_router.include_router(integration.router)
api_router.include_router(moderation.router)
api_router.include_router(knowledge_admin.router)
api_router.include_router(promotion.router)
api_router.include_router(enterprise.router)
api_router.include_router(wechat.router)
api_router.include_router(wechat_pay.router)
api_router.include_router(membership.router)
api_router.include_router(security.router)
api_router.include_router(ab_testing.router)
api_router.include_router(funnel_analysis.router)
api_router.include_router(channel_tracking.router)
api_router.include_router(home.router)
api_router.include_router(cross_domain.router)
api_router.include_router(video_consultation.router)
