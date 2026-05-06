"""输入安全防护模块"""
import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SanitizeResult:
    success: bool
    cleaned_text: str
    blocked_reason: Optional[str] = None
    risk_level: str = "low"


class InputSanitizer:
    """输入安全防护 - 防止Prompt注入、超长文本等攻击"""

    MAX_MESSAGE_LENGTH = 2000
    MAX_SYSTEM_PROMPT_LENGTH = 4000

    PROMPT_INJECTION_PATTERNS = [
        r"忽略.*(之前|所有|的)?(指令|指示|规则|instructions)",
        r"ignore\s+(all\s+)?(previous\s+)?(instructions|commands)",
        r"(你|现在)是\s*(一个?|款)?[\S]+(不是|而是)",
        r"(forget|remove|delete)\s+(all\s+)?(previous|your|my)",
        r"disregard\s+(all\s+)?(previous|your|my|instructions)",
        r"system\s*prompt\s*[:=]",
        r"\[(system|SYSTEM)\]",
        r"<(system|SYSTEM)>",
        r"新的\s*(system|系统)\s*指令",
        r"覆写.*(system|系统)",
        r"假装.*(你|自己是)",
        r"你现在可以.*(无视|突破)",
        r"(不顾|无视|突破).*(限制|规则|安全)",
        r"暂时.*(关闭|禁用|停止).*(审核|过滤)",
    ]

    SENSITIVE_PATTERNS = [
        r"\b\d{15,18}\b",  # 身份证号
        r"\b\d{4}[-/]\d{2}[-/]\d{2,4}\b",  # 日期
        r"password\s*[:=]\s*\S+",
        r"api[_-]?key\s*[:=]\s*\S+",
        r"secret\s*[:=]\s*\S+",
        r"token\s*[:=]\s*\S+",
    ]

    DANGEROUS_CHARS = [
        "<script",
        "javascript:",
        "onerror=",
        "onclick=",
        "onload=",
        "<iframe",
        "vbscript:",
        "expression\(",
    ]

    def __init__(self):
        self._inject_patterns = [re.compile(p, re.IGNORECASE) for p in self.PROMPT_INJECTION_PATTERNS]
        self._sensitive_patterns = [re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_PATTERNS]
        self._dangerous_chars_lower = [d.lower() for d in self.DANGEROUS_CHARS]

    def sanitize(self, user_input: str) -> SanitizeResult:
        """
        全面检测和清理用户输入
        """
        if not user_input:
            return SanitizeResult(
                success=True,
                cleaned_text="",
                risk_level="low"
            )

        text = user_input
        risk_level = "low"
        blocked_reason = None

        length_result = self._check_length(text)
        if not length_result.success:
            return length_result

        inject_result = self._check_prompt_injection(text)
        if not inject_result.success:
            return inject_result

        dangerous_result = self._check_dangerous_chars(text)
        if not dangerous_result.success:
            return dangerous_result

        text = self._clean_html_tags(text)
        text = self._normalize_whitespace(text)

        return SanitizeResult(
            success=True,
            cleaned_text=text.strip(),
            risk_level=risk_level
        )

    def _check_length(self, text: str) -> SanitizeResult:
        """检查文本长度"""
        if len(text) > self.MAX_MESSAGE_LENGTH:
            return SanitizeResult(
                success=False,
                cleaned_text=text[:self.MAX_MESSAGE_LENGTH],
                blocked_reason=f"消息长度超过限制({self.MAX_MESSAGE_LENGTH}字符)",
                risk_level="medium"
            )
        return SanitizeResult(success=True, cleaned_text=text)

    def _check_prompt_injection(self, text: str) -> SanitizeResult:
        """检测Prompt注入攻击"""
        for pattern in self._inject_patterns:
            match = pattern.search(text)
            if match:
                logger.warning(
                    f"Prompt injection detected: {text[:50]}...",
                    extra={"pattern": pattern.pattern, "match": match.group()}
                )
                return SanitizeResult(
                    success=False,
                    cleaned_text=text,
                    blocked_reason="检测到不安全的输入内容",
                    risk_level="high"
                )
        return SanitizeResult(success=True, cleaned_text=text)

    def _check_dangerous_chars(self, text: str) -> SanitizeResult:
        """检查危险字符和HTML标签"""
        text_lower = text.lower()
        for dangerous in self._dangerous_chars_lower:
            if dangerous in text_lower:
                logger.warning(f"Dangerous content detected: {dangerous}")
                return SanitizeResult(
                    success=False,
                    cleaned_text=text,
                    blocked_reason="检测到潜在的恶意内容",
                    risk_level="high"
                )
        return SanitizeResult(success=True, cleaned_text=text)

    def _clean_html_tags(self, text: str) -> str:
        """清理HTML标签"""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """规范化空白字符"""
        text = re.sub(r'\s+', ' ', text)
        return text

    def extract_sensitive_info(self, text: str) -> list[dict]:
        """提取敏感信息（用于日志脱敏）"""
        findings = []
        for pattern in self._sensitive_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                findings.append({
                    "type": "sensitive",
                    "pattern": pattern.pattern,
                    "match": match.group()[:10] + "***",
                    "position": match.span()
                })
        return findings

    def mask_sensitive_info(self, text: str) -> str:
        """脱敏处理"""
        for pattern in self._sensitive_patterns:
            text = pattern.sub(lambda m: m.group()[:4] + "****", text)
        return text


class SystemPromptValidator:
    """系统提示词验证器"""

    MAX_OVERRIDE_ATTEMPTS = 3
    FORBIDDEN_KEYWORDS = [
        "忽略", "无视", "忘记", "disregard", "ignore",
        "绕过", "bypass", "突破", "break",
        "你不再是", "you are not", "you were never",
    ]

    def validate(self, system_prompt: str) -> SanitizeResult:
        """验证系统提示词是否安全"""
        if len(system_prompt) > SystemPromptValidator.MAX_OVERRIDE_ATTEMPTS * 1000:
            return SanitizeResult(
                success=False,
                cleaned_text=system_prompt,
                blocked_reason="系统提示词过长",
                risk_level="medium"
            )

        prompt_lower = system_prompt.lower()
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword.lower() in prompt_lower:
                logger.warning(f"Forbidden keyword in system prompt: {keyword}")

        return SanitizeResult(
            success=True,
            cleaned_text=system_prompt,
            risk_level="low"
        )


_input_sanitizer: Optional[InputSanitizer] = None


def get_input_sanitizer() -> InputSanitizer:
    global _input_sanitizer
    if _input_sanitizer is None:
        _input_sanitizer = InputSanitizer()
    return _input_sanitizer


def sanitize_user_input(user_input: str) -> SanitizeResult:
    """便捷函数：sanitize user input"""
    sanitizer = get_input_sanitizer()
    return sanitizer.sanitize(user_input)
