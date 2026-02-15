"""邮件服务模块

向后兼容导出（2026-01-22）
"""
from .core import EmailService, email_service
from .templates import (
    get_password_reset_html_template,
    get_password_reset_text_template,
    get_email_verification_html_template,
    get_email_verification_text_template,
)
from .verification import email_verification_service
from .storage import ResetTokenData as EmailServiceResetTokenData
from .password_reset import password_reset_service

# 导出常量以保持测试兼容
from .core import _EMAIL_VERIFY_TOKEN_TTL_SECONDS

__all__ = [
    "EmailService",
    "email_service",
    "email_verification_service",
    "password_reset_service",
    "get_password_reset_html_template",
    "get_password_reset_text_template",
    "get_email_verification_html_template",
    "get_email_verification_text_template",
    "_EMAIL_VERIFY_TOKEN_TTL_SECONDS",
]
