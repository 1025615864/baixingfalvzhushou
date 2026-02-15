"""邮件服务存储模块

提供内存存储用于缓存不可用时的备用，并解决循环导入问题。
"""
from typing_extensions import TypedDict


class ResetTokenData(TypedDict):
    user_id: int
    email: str
    expires_at: str
    used: bool


class EmailVerificationTokenData(TypedDict):
    user_id: int
    email: str
    expires_at: str
    used: bool


# 内存存储（缓存不可用时备用）
_reset_tokens: dict[str, ResetTokenData] = {}
_email_verification_tokens: dict[str, EmailVerificationTokenData] = {}
