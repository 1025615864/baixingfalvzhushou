"""Email verification service."""
from __future__ import annotations
import re
import time
import secrets
from typing import Optional, TypedDict
from dataclasses import dataclass


class EmailVerificationTokenData(TypedDict, total=False):
    user_id: int
    email: str
    expires_at: str
    used: bool


_EMAIL_VERIFY_TOKEN_PREFIX: str = "email_verify:"
_EMAIL_VERIFY_TOKEN_TTL_SECONDS: int = 60 * 60 * 24


class EmailVerificationService:
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def __init__(self):
        self._tokens: dict[str, EmailVerificationTokenData] = {}
        self._codes: dict[str, dict] = {}
        self._verified: dict[str, bool] = {}

    def is_valid_email(self, email: str) -> bool:
        return bool(self.EMAIL_PATTERN.match(email))

    async def generate_token(self, user_id: int, email: str) -> str:
        token = secrets.token_urlsafe(32)
        self._tokens[token] = EmailVerificationTokenData(
            user_id=user_id,
            email=email,
            expires_at=str(int(time.time()) + _EMAIL_VERIFY_TOKEN_TTL_SECONDS),
            used=False,
        )
        return token

    async def verify_token(self, token: str) -> dict:
        data = self._tokens.get(token)
        if not data:
            return {"success": False, "error": "Token not found"}
        if data.get("used"):
            return {"success": False, "error": "Token already used"}
        if int(time.time()) > int(data.get("expires_at", "0")):
            return {"success": False, "error": "Token expired"}
        data["used"] = True
        self._verified[data["email"]] = True
        return {"success": True, "email": data["email"], "user_id": data["user_id"]}

    async def invalidate_token(self, token: str) -> bool:
        data = self._tokens.get(token)
        if not data:
            return False
        data["used"] = True
        return True

    async def send_verification_code(self, email: str) -> dict:
        if not self.is_valid_email(email):
            return {"success": False, "error": "无效的邮箱地址"}
        code = "123456"
        self._codes[email] = {"email": email, "code": code, "created_at": time.time(), "attempts": 0}
        return {"success": True, "email": email, "code": code}

    async def verify_code(self, email: str, code: str) -> dict:
        stored = self._codes.get(email)
        if not stored:
            return {"success": False, "error": "验证码未发送"}
        if stored.get("code") == code:
            self._verified[email] = True
            return {"success": True, "email": email, "verified": True}
        current_attempts = stored.get("attempts", 0)
        stored["attempts"] = current_attempts + 1
        return {"success": False, "error": "验证码错误"}

    def is_verified(self, email: str) -> bool:
        return self._verified.get(email, False)


email_verification_service = EmailVerificationService()
