"""FAQ服务

⚠️ 已迁移到 services/faq/
⚠️ 本文件仅用于向后兼容，请使用新导入路径

迁移时间: 2026-01-22
"""
from .faq import (
    faq_service,
    FAQService,
)

__all__ = [
    "faq_service",
    "FAQService",
]
