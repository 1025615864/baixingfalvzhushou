from __future__ import annotations

from pydantic import BaseModel


class LegalProfessionalResult(BaseModel):
    is_legal_professional: bool = False
    specialty: str | None = None
    confidence: float = 0.0


class ContentQualityResult(BaseModel):
    quality_score: float = 0.0
    issues: list[str] = []
    suggestions: list[str] = []


class NewsQualityService:
    pass
