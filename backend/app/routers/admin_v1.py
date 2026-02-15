"""
Admin V1 Router - 统一的管理后台路由入口
将所有管理功能挂载到 /api/v1/admin/* 路径下
"""

from fastapi import APIRouter

# 导入现有的管理路由
from .lawfirm import firms as lawfirm_firms
from .settlement import admin as settlement_admin
from .forum import posts as forum_posts
from .payment import admin_ops as payment_admin
from .notification import router as notification_router
from .document_templates import router as document_templates_router
from .consultation_templates import router as consultation_templates_router
from .system_admin import config as system_config

router = APIRouter(prefix="/v1/admin", tags=["管理后台V1"])

# ==================== 律所管理 ====================
# 挂载律所管理路由到 /api/v1/admin/law-firms
router.include_router(
    lawfirm_firms.router,
    prefix="/law-firms",
    tags=["律所管理"]
)

# ==================== 提现管理 ====================
# 挂载提现管理路由到 /api/v1/admin/withdrawals
router.include_router(
    settlement_admin.router,
    prefix="/withdrawals",
    tags=["提现管理"]
)

# ==================== 帖子管理 ====================
# 挂载帖子管理路由到 /api/v1/admin/posts
router.include_router(
    forum_posts.router,
    prefix="/posts",
    tags=["帖子管理"]
)

# ==================== 支付回调管理 ====================
# 挂载支付回调路由到 /api/v1/admin/payment/callbacks
router.include_router(
    payment_admin.router,
    prefix="/payment/callbacks",
    tags=["支付回调管理"]
)

# ==================== 结算统计 ====================
# 挂载结算路由到 /api/v1/admin/payment/settlement
router.include_router(
    settlement_admin.router,
    prefix="/payment/settlement",
    tags=["结算管理"]
)

# ==================== 系统通知管理 ====================
# 挂载通知路由到 /api/v1/admin/notifications
# 注意：notification_router 已有 /notifications 前缀，这里不需要重复添加
router.include_router(
    notification_router,
    tags=["系统通知管理"]
)

# ==================== 文档模板管理 ====================
# 挂载文档模板路由到 /api/v1/admin/document-templates
router.include_router(
    document_templates_router,
    prefix="/document-templates",
    tags=["文档模板管理"]
)

# ==================== 咨询模板管理 ====================
# 挂载咨询模板路由到 /api/v1/admin/consultation-templates
router.include_router(
    consultation_templates_router,
    prefix="/consultation-templates",
    tags=["咨询模板管理"]
)

# ==================== 系统设置 ====================
# 挂载系统设置路由到 /api/v1/admin/settings
router.include_router(
    system_config.router,
    prefix="/settings",
    tags=["系统设置"]
)
