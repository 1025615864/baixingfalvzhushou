from __future__ import annotations

from pydantic import BaseModel, Field


class InteractionRequest(BaseModel):
    content_type: str
    content_id: int
    action: str
    duration: float | None = None


class OnboardingAnswer(BaseModel):
    question_id: str
    answer: str | list[str]
