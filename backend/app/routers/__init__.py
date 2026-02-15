"""API路由"""

import logging

from .settlement import router as settlement_router
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# Import admin_v1 router for unified admin API
from . import admin_v1

from . import (
    ai_quality,
    analytics,
    calendar,
    channel_tracking,
    contracts,
    cross_domain,
    document,
    forum,
    home,
    knowledge,
    lawfirm,
    news,
    notification,
    payment,
    search,
    upload,
    user,
    feedback,
    reviews,
    lawyer_recommendation,
    faq,
    recommendation,
    points,
    admin_monitor,
    news_recommendation,
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
    funnel_analysis)

# Import admin.py explicitly to avoid conflict with system_admin directory
from . import admin

try:
    from . import ai
except Exception:
    logger.exception("Failed to import ai router")
    ai = None

try:
    from . import system
except Exception:
    logger.exception("Failed to import system router")
    system = None

api_router = APIRouter()
legacy_api_router = APIRouter()

# Include unified admin v1 router
api_router.include_router(admin_v1.router)

if ai is not None:
    api_router.include_router(ai.router)
api_router.include_router(ai_quality.router)
api_router.include_router(user.router)
legacy_api_router.include_router(user.router)
api_router.include_router(forum.router)
api_router.include_router(news.router)
api_router.include_router(lawfirm.router)
api_router.include_router(admin.router)
api_router.include_router(upload.router)
api_router.include_router(knowledge.router)
api_router.include_router(notification.router)
if system is not None:
    system_router = getattr(system, "router", None)
    if system_router is not None:
        api_router.include_router(system_router)
api_router.include_router(document.router)
# document_templates 和 consultation_templates 通过 admin_v1 挂载
api_router.include_router(contracts.router)
api_router.include_router(search.router)
api_router.include_router(payment.router)
api_router.include_router(calendar.router)
api_router.include_router(feedback.router)
# Include settlement router (backward compatibility)

api_router.include_router(settlement_router)
api_router.include_router(reviews.router)
api_router.include_router(lawyer_recommendation.router)
api_router.include_router(analytics.router)
api_router.include_router(faq.router)
api_router.include_router(recommendation.router)
api_router.include_router(points.router)
api_router.include_router(admin_monitor.router)
api_router.include_router(news_recommendation.router)

# Import system_admin directory router
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

# 垂直频道路由（婚姻、劳动法律服务等）
api_router.include_router(vertical_channel.router)

# 模块联动路由（咨询→文书→律师）
api_router.include_router(integration.router)

# 内容审核路由
api_router.include_router(moderation.router)

# 知识库管理路由
api_router.include_router(knowledge_admin.router)

# SEO/裂变推广路由
api_router.include_router(promotion.router)

# 企业合规 SaaS 路由
api_router.include_router(enterprise.router)

# 微信生态路由（登录、消息、公众号）
api_router.include_router(wechat.router)

# 微信支付路由（统一下单、支付配置、订单查询）
api_router.include_router(wechat_pay.router)

# 会员体系路由
api_router.include_router(membership.router)

# 数据安全路由
api_router.include_router(security.router)

# A/B 测试路由
api_router.include_router(ab_testing.router)

# 漏斗分析路由
api_router.include_router(funnel_analysis.router)

# 营销渠道追踪路由
api_router.include_router(channel_tracking.router)

# 首页路由
api_router.include_router(home.router)

# Cross-Domain 域名管理路由
api_router.include_router(cross_domain.router)

 

