"""Content safety filter service."""
from __future__ import annotations
import enum
import re
from dataclasses import dataclass, field
from typing import Optional


class RiskLevel(enum.Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass
class SafetyCheckResult:
    risk_level: RiskLevel = RiskLevel.SAFE
    should_log: bool = False
    suggestion: Optional[str] = None
    triggered_rules: list[str] = field(default_factory=list)


class ContentSafetyFilter:
    BLOCKED_PATTERNS = ["杀人", "自杀方法", "制造炸弹"]
    HIGH_RISK_PATTERNS = ["自杀", "自残", "伤害他人"]
    SENSITIVE_PATTERNS = {"政治敏感": ["政府腐败", "政治"]}

    PHONE_PATTERN = re.compile(r"1[3-9]\d{9}")
    ID_CARD_PATTERN = re.compile(r"\d{17}[\dXx]")

    def check_input(self, text: str) -> SafetyCheckResult:
        for p in self.BLOCKED_PATTERNS:
            if p in text:
                return SafetyCheckResult(risk_level=RiskLevel.BLOCKED, should_log=True, suggestion="该内容已被拦截", triggered_rules=[f"blocked:{p}"])
        for p in self.HIGH_RISK_PATTERNS:
            if p in text:
                return SafetyCheckResult(risk_level=RiskLevel.HIGH, should_log=True, suggestion=None, triggered_rules=[f"high_risk:{p}"])
        for category, patterns in self.SENSITIVE_PATTERNS.items():
            for p in patterns:
                if p in text:
                    return SafetyCheckResult(risk_level=RiskLevel.MEDIUM, should_log=True, suggestion=None, triggered_rules=[f"sensitive:{category}"])
        return SafetyCheckResult(risk_level=RiskLevel.SAFE, should_log=False, suggestion=None, triggered_rules=[])

    def sanitize_output(self, text: str) -> str:
        text = self.PHONE_PATTERN.sub("[电话号码已隐藏]", text)
        text = self.ID_CARD_PATTERN.sub("[身份证号已隐藏]", text)
        return text
