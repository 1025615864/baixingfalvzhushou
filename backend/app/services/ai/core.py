"""AI core utilities."""
from __future__ import annotations
from typing import Optional


class AICore:
    SYSTEM_PROMPT = "你是\"百姓法律助手\"的AI法律咨询员，请根据中国法律为用户提供专业的法律咨询意见。"
    SYSTEM_PROMPT_V2 = (
        "你是\"百姓法律助手\"的AI法律咨询员。\n"
        "输出优先级：结论摘要 > 法律依据 > 详细分析。\n"
        "请在回答中包含结论摘要和法律依据。"
    )

    @classmethod
    def _system_prompt_for_version(cls, version: Optional[str]) -> str:
        if version is None:
            return cls.SYSTEM_PROMPT
        v = str(version).strip().lower()
        if v in ("v2", "2", "beta"):
            return cls.SYSTEM_PROMPT_V2
        return cls.SYSTEM_PROMPT

    @classmethod
    def _encoding_for_model(cls, model: Optional[str]):
        try:
            import tiktoken
            if not model:
                return tiktoken.get_encoding("cl100k_base")
            try:
                return tiktoken.encoding_for_model(model)
            except (KeyError, ValueError):
                return tiktoken.get_encoding("cl100k_base")
        except ImportError:
            return None

    @classmethod
    def _count_tokens(cls, text: Optional[str], model: str = "gpt-4") -> int:
        if not text:
            return 0
        enc = cls._encoding_for_model(model)
        if enc is None:
            return len(str(text)) // 4
        return len(enc.encode(str(text)))

    @classmethod
    def _estimate_cost_usd(cls, model: Optional[str], prompt_tokens: int, completion_tokens: int) -> Optional[float]:
        if not model:
            return None
        m = model.lower()
        pricing = {
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (5.00, 15.00),
            "gpt-3.5-turbo": (0.50, 1.50),
        }
        matched = None
        for key in pricing:
            if m.startswith(key):
                matched = key
                break
        if matched is None:
            return None
        p_in, p_out = pricing[matched]
        return (prompt_tokens / 1_000_000) * p_in + (completion_tokens / 1_000_000) * p_out
