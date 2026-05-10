from __future__ import annotations

from enum import Enum
from typing import Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResponseStrategy(str, Enum):
    DIRECT = "direct"
    REDIRECT = "redirect"
    CLARIFY = "clarify"


class DisclaimerManager:
    GENERAL_DISCLAIMER: str = "\n\n---\n\n📌 **重要提示**：以上内容仅供参考，不构成正式法律意见。具体法律问题请咨询专业律师。"

    RISK_DISCLAIMERS: dict[RiskLevel, str] = {
        RiskLevel.HIGH: "\n\n---\n\n🔴 **高风险提示**：您咨询的问题涉及较高法律风险，AI 回答仅供初步了解。请务必咨询专业律师获取针对性意见。",
        RiskLevel.MEDIUM: "\n\n---\n\n🟡 **风险提示**：此类问题情况复杂，建议结合实际情况咨询专业律师。",
    }

    def get_disclaimer(self, *, risk_level: RiskLevel = RiskLevel.LOW,
                       strategy: ResponseStrategy = ResponseStrategy.DIRECT) -> str:
        parts: list[str] = []
        risk = self.RISK_DISCLAIMERS.get(risk_level)
        if risk:
            parts.append(risk)

        if strategy == ResponseStrategy.REDIRECT:
            parts.append("\n\n建议您通过平台预约专业律师咨询。")

        if not parts:
            parts.append(self.GENERAL_DISCLAIMER)

        return "\n".join(parts)
