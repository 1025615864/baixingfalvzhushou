"""内容审核服务 - 三级审核流水线"""
from dataclasses import dataclass
from typing import Optional, List
import asyncio

from ..utils.sensitive_words import sensitive_filter
from ..clients import ai_client


@dataclass
class ModerationResult:
    blocked: bool = False
    needs_review: bool = False
    reason: Optional[str] = None
    matched_words: Optional[List[str]] = None
    confidence: float = 0.0
    level: str = "pass"


class ModerationService:
    def __init__(self, ai_client_instance=None):
        self.sensitive_filter = sensitive_filter
        self.ai_client = ai_client_instance or ai_client

    async def check_content(self, content: str) -> ModerationResult:
        word_result = self.sensitive_filter.check(content)
        if word_result[0]:
            return ModerationResult(
                blocked=True,
                reason=f"包含敏感词: {', '.join(word_result[1])}",
                matched_words=word_result[1],
                level="keyword"
            )

        if self.ai_client:
            try:
                ai_result = await asyncio.wait_for(
                    self.ai_client.analyze_content(content),
                    timeout=2.0
                )
                if ai_result.confidence > 0.9:
                    return ModerationResult(
                        blocked=True,
                        reason=ai_result.reason,
                        confidence=ai_result.confidence,
                        level="ai"
                    )
                elif ai_result.confidence > 0.5:
                    return ModerationResult(
                        blocked=False,
                        needs_review=True,
                        reason="内容待人工审核",
                        confidence=ai_result.confidence,
                        level="ai"
                    )
            except asyncio.TimeoutError:
                pass

        return ModerationResult(blocked=False, level="pass")

    def check_contact_info(self, content: str) -> bool:
        import re
        phone_pattern = r"1[3-9]\d{9}"
        wechat_pattern = r"微信[:：]?\s*[a-zA-Z0-9_]+"
        email_pattern = r"[\w.-]+@[\w.-]+\.\w+"

        return bool(
            re.search(phone_pattern, content) or
            re.search(wechat_pattern, content) or
            re.search(email_pattern, content)
        )

    async def check_legal_content(self, content: str) -> dict:
        if self.ai_client:
            try:
                return await self.ai_client.check_legal_advice(content)
            except Exception:
                pass
        return {"is_legal": True, "warnings": []}


moderation_service = ModerationService()
