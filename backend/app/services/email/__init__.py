"""Email service with sub-modules."""
from __future__ import annotations
from typing import Optional
from app.services.email.optimizer import EmailOptimizer
from app.services.email.verification import EmailVerificationService
from app.services.email.storage import EmailStorage


class EmailService:
    def __init__(self):
        self.optimizer = EmailOptimizer()
        self.verification = EmailVerificationService()
        self.storage = EmailStorage()

    async def send_email(self, to: str, subject: str, body: str, **kwargs) -> dict:
        optimized = self.optimizer.optimize(subject=subject, body=body)
        result = {"success": True, "to": to, "subject": optimized["subject"], "message_id": f"msg_{id(to)}"}
        self.storage.store(result)
        return result


email_service = EmailService()
