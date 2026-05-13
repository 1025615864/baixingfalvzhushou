from __future__ import annotations

from pydantic import BaseModel, Field


class InteractionRequest(BaseModel):
    content_type: str
    content_id: int | str = 0
    action: str = ""
    duration: float | None = None
    tags: list[str] = []
    interaction_type: str = ""
    weight: float = 1.0


class OnboardingAnswer(BaseModel):
    question_id: str = ""
    answer: str | list[str] = ""
    answers: dict = {}
