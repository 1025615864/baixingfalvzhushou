"""AI model configuration."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIModelConfig:
    model_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    weight: int = 1
