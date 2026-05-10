"""Content moderation service."""
from __future__ import annotations
import re
from typing import Optional


class KeywordFilter:
    def __init__(self):
        self._keywords: dict[str, dict] = {}
        self._next_id = 1

    def add_keyword(self, keyword: str, category: str = "general", severity: str = "medium") -> dict:
        kid = f"KW-{self._next_id:04d}"
        self._next_id += 1
        self._keywords[keyword] = {"keyword_id": kid, "keyword": keyword, "category": category, "severity": severity}
        return {"keyword_id": kid, "keyword": keyword, "category": category}

    def check_content(self, content: str, categories: Optional[list[str]] = None) -> dict:
        matched = []
        risk_score = 0
        for kw, info in self._keywords.items():
            if categories and info["category"] not in categories:
                continue
            if kw in content:
                matched.append(info)
                severity_scores = {"high": 30, "medium": 20, "low": 10}
                risk_score += severity_scores.get(info["severity"], 10)
        return {"is_safe": len(matched) == 0, "risk_score": risk_score, "matched_count": len(matched), "matched_keywords": matched}

    def get_keywords_by_category(self, category: str) -> list[dict]:
        return [info for info in self._keywords.values() if info["category"] == category]


class ContentModerationService:
    def __init__(self):
        self._contents: dict[int, dict] = {}
        self._next_id = 1
        self._keyword_filter = KeywordFilter()

    async def submit_content(self, user_id: int, content_type: str, content: str) -> dict:
        cid = self._next_id
        self._next_id += 1
        self._contents[cid] = {"id": cid, "user_id": user_id, "content_type": content_type, "content": content, "status": "pending", "check_result": None, "final_decision": None}
        return {"content_id": cid, "status": "pending", "risk_score": 0}

    async def ai_review(self, content_id: int) -> dict:
        entry = self._contents.get(content_id)
        if not entry:
            return {"success": False, "error": "内容不存在"}
        content = entry.get("content", "")
        flags = []
        is_safe = True
        unsafe_keywords = {"诈骗": "potential_fraud", "赌博": "gambling", "色情": "pornographic"}
        for kw, flag in unsafe_keywords.items():
            if kw in content:
                flags.append(flag)
                is_safe = False
        confidence = 0.95 if is_safe else 0.85
        entry["check_result"] = {"risk_level": "low" if is_safe else "high", "flags": flags}
        return {"success": True, "is_safe": is_safe, "confidence": confidence, "flags": flags}

    async def make_decision(self, content_id: int, decision: str = "auto") -> dict:
        entry = self._contents.get(content_id)
        if not entry:
            return {"success": False, "error": "内容不存在"}
        if decision == "auto":
            check = entry.get("check_result", {})
            final = "approved" if check.get("risk_level", "high") == "low" else "rejected"
        else:
            final = decision
        entry["final_decision"] = final
        return {"success": True, "decision": final}

    async def get_moderation_stats(self) -> dict:
        total = len(self._contents)
        approved = sum(1 for c in self._contents.values() if c.get("final_decision") == "approved")
        return {"total_content": total, "approved": approved, "approval_rate": approved / total if total > 0 else 0.0}

    async def report_content(self, reporter_id: int, content_id: int, reason: str) -> dict:
        return {"report_id": content_id, "status": "pending"}

    def get_total_checks(self) -> int:
        return len(self._contents)

    def get_blocked_count(self) -> int:
        return sum(1 for c in self._contents.values() if c.get("final_decision") == "rejected")

    def get_warning_count(self) -> int:
        return sum(1 for c in self._contents.values() if c.get("check_result", {}).get("risk_level") == "high")

    def get_passed_count(self) -> int:
        return sum(1 for c in self._contents.values() if c.get("final_decision") == "approved")

    def get_block_rate(self) -> float:
        total = len(self._contents)
        if total == 0:
            return 0.0
        return round(self.get_blocked_count() / total * 100, 2)

    def get_category_count(self, category: str) -> int:
        return sum(1 for c in self._contents.values() if c.get("content_type") == category)


content_moderation_service = ContentModerationService()


class ContentFilter:
    def __init__(self, custom_words: list[str] | None = None, ad_threshold: int = 2, check_url: bool = True, check_phone: bool = True):
        self.sensitive_words: set[str] = set(custom_words or [])
        self.ad_words: set[str] = set()
        self.ad_threshold: int = ad_threshold
        self.check_url: bool = check_url
        self.check_phone: bool = check_phone

    def apply_config(self, sensitive_words: list[str] | None = None, ad_words: list[str] | None = None, ad_threshold: int | None = None, check_url: bool | None = None, check_phone: bool | None = None) -> None:
        if sensitive_words is not None:
            self.sensitive_words = {str(w).strip() for w in sensitive_words if str(w).strip()}
        if ad_words is not None:
            self.ad_words = {str(w).strip() for w in ad_words if str(w).strip()}
        if ad_threshold is not None:
            self.ad_threshold = ad_threshold
        if check_url is not None:
            self.check_url = check_url
        if check_phone is not None:
            self.check_phone = check_phone

    def check_content(self, content: str) -> tuple[bool, str, list[str]]:
        if not content:
            return True, "", []
        content_lower = content.lower()
        matched_sensitive = [w for w in self.sensitive_words if w.lower() in content_lower]
        matched_ads = [w for w in self.ad_words if w.lower() in content_lower]
        if matched_sensitive:
            return False, "内容包含敏感词汇", matched_sensitive
        if len(matched_ads) >= self.ad_threshold:
            return False, "内容疑似广告", matched_ads
        return True, "", []

    def filter_content(self, content: str, replacement: str = "***") -> str:
        if not content:
            return content
        result = content
        for word in list(self.sensitive_words) + list(self.ad_words):
            result = re.compile(re.escape(word), re.IGNORECASE).sub(replacement, result)
        return result

    def get_risk_level(self, content: str) -> str:
        passed, _, matched = self.check_content(content)
        if passed:
            return "safe"
        if len(matched) >= 3:
            return "danger"
        return "warning"


async def submit_content_for_moderation(user_id: int, content_type: str, content: str) -> dict:
    return await content_moderation_service.submit_content(user_id, content_type, content)


async def ai_review_content(content_id: int) -> dict:
    return await content_moderation_service.ai_review(content_id)


async def get_moderation_stats() -> dict:
    return await content_moderation_service.get_moderation_stats()
