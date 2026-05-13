"""Email service with sub-modules."""
from __future__ import annotations
import hashlib
import hmac
import os
import time
from typing import Any, Optional
from app.services.email.optimizer import EmailOptimizer
from app.services.email.verification import EmailVerificationService
from app.services.email.storage import EmailStorage

_RESET_SECRET = os.environ.get("EMAIL_RESET_SECRET", "baixing-reset-secret-key-2026")


class EmailService:
    def __init__(self):
        self.optimizer = EmailOptimizer()
        self.verification = EmailVerificationService()
        self.storage = EmailStorage()
        self._token_store: dict[str, dict[str, Any]] = {}

    async def send_email(self, to: str, subject: str, body: str, **kwargs) -> dict:
        optimized = self.optimizer.optimize(subject=subject, body=body)
        result = {"success": True, "to": to, "subject": optimized["subject"], "message_id": f"msg_{id(to)}"}
        self.storage.store(result)
        return result

    async def generate_reset_token(self, user_id: int, email: str) -> str:
        ts = str(int(time.time()))
        payload = f"{user_id}:{email}:{ts}"
        sig = hmac.new(_RESET_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        token = f"{payload}:{sig}"
        self._token_store[token] = {"user_id": user_id, "email": email, "ts": ts}
        return token

    async def verify_reset_token(self, token: str) -> Optional[dict]:
        if token in self._token_store:
            return self._token_store[token]
        parts = token.split(":")
        if len(parts) != 4:
            return None
        user_id_str, email, ts, sig = parts
        payload = f"{user_id_str}:{email}:{ts}"
        expected_sig = hmac.new(_RESET_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected_sig):
            return None
        return {"user_id": int(user_id_str), "email": email}

    async def configure_from_db(self, db) -> bool:
        return True

    async def generate_email_verification_token(self, user_id: int, email: str) -> str:
        return await self.verification.generate_token(user_id, email)

    async def verify_email_verification_token(self, token: str) -> Optional[dict]:
        result = await self.verification.verify_token(token)
        if result.get("success"):
            return {"user_id": result["user_id"], "email": result["email"]}
        return None

    async def send_email_verification_email(self, email: str, verify_url: str, user_id: int = None) -> bool:
        return True


email_service = EmailService()
