"""News quality service."""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class LegalProfessionalResult:
    is_legal_professional: bool = False
    profession_type: Optional[str] = None
    confidence: float = 0.0
    verified: bool = False


@dataclass
class ContentQualityResult:
    quality_score: float = 0.0
    readability_score: float = 0.0
    originality_score: float = 0.0
    issues: list[str] = field(default_factory=list)
    passed: bool = False


class NewsQualityService:
    def __init__(self):
        self._quality_records: dict[int, dict] = {}

    async def evaluate_article(self, article_id: int, title: str = "", content: str = "") -> dict:
        score = 0
        issues = []
        if not title or len(title) < 5:
            issues.append("标题过短")
        else:
            score += 30
        if not content or len(content) < 50:
            issues.append("内容过短")
        else:
            score += 40
        if title and content:
            score += 30
        result = {"article_id": article_id, "quality_score": score, "issues": issues, "passed": score >= 60}
        self._quality_records[article_id] = result
        return result

    async def get_quality_record(self, article_id: int) -> Optional[dict]:
        return self._quality_records.get(article_id)

    async def get_quality_stats(self) -> dict:
        total = len(self._quality_records)
        passed = sum(1 for r in self._quality_records.values() if r.get("passed"))
        return {"total_evaluated": total, "passed": passed, "pass_rate": passed / total if total > 0 else 0.0}

    def check_legal_professional(self, content: str) -> LegalProfessionalResult:
        return LegalProfessionalResult()

    def evaluate_content_quality(self, content: str) -> ContentQualityResult:
        score = min(100.0, len(content) * 0.1)
        return ContentQualityResult(
            quality_score=score,
            readability_score=score * 0.8,
            originality_score=score * 0.9,
            passed=score >= 60,
        )


news_quality_service = NewsQualityService()
