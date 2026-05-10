"""AI response strategy service."""
from __future__ import annotations
import enum


class ResponseStrategy(enum.Enum):
    GENERAL_LEGAL = "general_legal"
    REDIRECT = "redirect"
