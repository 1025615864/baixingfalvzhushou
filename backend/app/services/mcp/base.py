"""MCP base module."""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional


class ToolCategory(str, Enum):
    CALCULATOR = "calculator"
    SEARCH = "search"
    DOCUMENT = "document"
    CONSULTATION = "consultation"
    KNOWLEDGE = "knowledge"
    LAWFIRM = "lawfirm"
    UTILITY = "utility"


class ToolPermission(str, Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    VIP = "vip"


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: Optional[str] = None


class BaseTool:
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    category: ToolCategory = ToolCategory.CALCULATOR
    permission: ToolPermission = ToolPermission.PUBLIC
    tags: list[str] = field(default_factory=list)

    async def execute(self, params: dict, context: dict) -> ToolResult:
        raise NotImplementedError
