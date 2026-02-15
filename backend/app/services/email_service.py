"""邮件服务

⚠️ 已迁移到 services/email/
⚠️ 本文件仅用于向后兼容，请使用新导入路径

迁移时间: 2026-01-22
"""
from typing_extensions import TypedDict
import secrets
from datetime import datetime, timedelta, timezone

from .cache_service import cache_service
from .email import (
    EmailService,
    email_service,
    get_password_reset_html_template,
    get_password_reset_text_template,
    get_email_verification_html_template,
    get_email_verification_text_template,
    _EMAIL_VERIFY_TOKEN_TTL_SECONDS as _EMAIL_VERIFY_TOKEN_TTL_SECONDS_IMPORTED,
)
from .email.storage import (
    ResetTokenData,
    EmailVerificationTokenData,
    _reset_tokens,
    _email_verification_tokens,
)
from . import email as _email_module

# ============================================================================
# 向后兼容：导出密码重置令牌相关的变量
# ============================================================================

_RESET_TOKEN_PREFIX = "password_reset_token:"
_RESET_TOKEN_TTL_SECONDS = 3600

# 导出邮箱验证常量（向后兼容）
_EMAIL_VERIFY_TOKEN_PREFIX = "email_verify_token:"
_EMAIL_VERIFY_TOKEN_TTL_SECONDS = 60 * 60 * 24  # 24小时

# 导入并重新导出模块（用于 monkeypatch 测试兼容）
password_reset_service = _email_module.password_reset_service
email_verification_service = _email_module.email_verification_service


__all__ = [
    "EmailService",
    "email_service",
    "email_verification_service",
    "password_reset_service",
    "get_password_reset_html_template",
    "get_password_reset_text_template",
    "get_email_verification_html_template",
    "get_email_verification_text_template",
    # 向后兼容变量
    "_reset_tokens",
    "_email_verification_tokens",
    "_EMAIL_VERIFY_TOKEN_TTL_SECONDS",
    "_EMAIL_VERIFY_TOKEN_PREFIX",
]
