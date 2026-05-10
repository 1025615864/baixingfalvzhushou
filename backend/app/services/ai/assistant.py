"""AI legal assistant service."""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass

from app.services.ai.session import SessionManager
from app.services.ai.core import AICore


@dataclass
class ParsedReference:
    content: str
    knowledge_id: Optional[int] = None
    similarity: float = 0.0


class AILegalAssistant:
    def __init__(self):
        self._session_manager = SessionManager()
        self.conversation_histories = self._session_manager.conversation_histories
        self._last_seen = self._session_manager._last_seen
        self._max_sessions = 100
        self._max_messages_per_session = 50
        self._disclaimer_manager = None

    def get_or_create_session(self, session_id: str) -> str:
        return self._session_manager.get_or_create_session(session_id)

    def clear_session(self, session_id: str) -> None:
        self._session_manager.clear_session(session_id)

    def _evict_if_needed(self) -> None:
        self._session_manager._evict_if_needed()

    def _append_disclaimer(self, answer: str, risk_level=None, strategy=None) -> str:
        if self._disclaimer_manager is None:
            try:
                from app.services.disclaimer import DisclaimerManager
                self._disclaimer_manager = DisclaimerManager()
            except Exception:
                return answer
        disclaimer = self._disclaimer_manager.get_disclaimer(risk_level=risk_level, strategy=strategy)
        if disclaimer:
            return f"{answer}\n\n---\n{disclaimer}"
        return answer

    def _normalize_history(self, history: list[dict]) -> list[dict]:
        return self._session_manager._normalize_history(history)

    def _count_tokens(self, text: str, model: str = "gpt-4") -> int:
        return AICore._count_tokens(text, model)

    def _estimate_cost_usd(self, model: Optional[str], prompt_tokens: int, completion_tokens: int) -> Optional[float]:
        return AICore._estimate_cost_usd(model, prompt_tokens, completion_tokens)

    def _build_context(self, references: list[tuple]) -> str:
        if not references:
            return "暂无相关法律条文参考"
        parts = []
        for i, (content, metadata, score) in enumerate(references, 1):
            parts.append(f"{i}. {content}")
        return "\n\n".join(parts)

    def _parse_references(self, references: list[tuple]) -> list[ParsedReference]:
        result = []
        for content, metadata, similarity in references:
            kid = metadata.get("knowledge_id")
            parsed_kid = None
            if kid is not None:
                try:
                    parsed_kid = int(kid)
                except (ValueError, TypeError):
                    parsed_kid = None
            result.append(ParsedReference(content=content, knowledge_id=parsed_kid, similarity=similarity))
        return result

    def _model_candidates(self) -> list[str]:
        try:
            from app.core.config import get_settings
            settings = get_settings()
            primary = getattr(settings, 'ai_model', '')
            fallbacks = getattr(settings, 'ai_fallback_models', []) or []
            candidates = [primary] + fallbacks
            return list(dict.fromkeys(c for c in candidates if c and c.strip()))
        except Exception:
            return []

    def _encoding_for_model(self, model: Optional[str]):
        return AICore._encoding_for_model(model)

    def _llm_for_model(self, model: str):
        try:
            from langchain_openai import ChatOpenAI
            from app.core.config import get_settings
            settings = get_settings()
            return ChatOpenAI(
                model=model,
                openai_api_key=settings.openai_api_key,
                openai_api_base=getattr(settings, 'openai_base_url', None),
            )
        except Exception:
            return None
