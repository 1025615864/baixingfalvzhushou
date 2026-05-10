"""Email storage service."""
from __future__ import annotations
from typing import Optional


_email_verification_tokens: dict[str, dict] = {}
_reset_tokens: dict[str, dict] = {}


class EmailStorage:
    def __init__(self):
        self._emails: list[dict] = []

    def store(self, email_data: dict) -> str:
        email_id = f"email_{len(self._emails)}"
        self._emails.append({"id": email_id, **email_data})
        return email_id

    def get(self, email_id: str) -> Optional[dict]:
        for e in self._emails:
            if e["id"] == email_id:
                return e
        return None

    def list_emails(self, limit: int = 100) -> list[dict]:
        return self._emails[:limit]
