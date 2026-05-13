from __future__ import annotations

from enum import Enum
from typing import Optional

from app.services.content_safety import RiskLevel
from app.services.ai_response_strategy import ResponseStrategy


class DisclaimerManager:
    GENERAL_DISCLAIMER: str = "\n\n---\n\n📌 **重要提示**：以上内容仅供参考，不构成正式法律意见。具体法律问题请咨询专业律师。"

    RISK_DISCLAIMERS: dict = {
        RiskLevel.HIGH: "\n\n---\n\n🔴 **高风险提示**：您咨询的问题涉及较高法律风险，AI 回答仅供初步了解。请务必咨询专业律师获取针对性意见。",
        RiskLevel.MEDIUM: "\n\n---\n\n🟡 **风险提示**：此类问题情况复杂，建议结合实际情况咨询专业律师。",
        RiskLevel.LOW: "\n\n---\n\n⚠️ **风险提示**：此问题可能存在一定法律风险，建议谨慎处理。",
    }

    REDIRECT_DISCLAIMER: str = "\n\n建议您通过平台预约专业律师咨询。"

    def get_disclaimer(self, *, risk_level=None, strategy=None) -> str:
        if risk_level is None and strategy is None:
            return self.GENERAL_DISCLAIMER

        parts: list[str] = []

        if risk_level is not None:
            risk_text = self.RISK_DISCLAIMERS.get(risk_level)
            if risk_text:
                parts.append(risk_text)

        if strategy == ResponseStrategy.REDIRECT:
            parts.append(self.REDIRECT_DISCLAIMER)

        if not parts:
            return self.GENERAL_DISCLAIMER

        return "\n".join(parts)
