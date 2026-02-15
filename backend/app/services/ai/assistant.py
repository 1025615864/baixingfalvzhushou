"""AI法律咨询助手服务

提供法律咨询对话的核心服务。
"""
from __future__ import annotations

import os
import time
import uuid
import logging
from collections.abc import AsyncGenerator
from typing import cast, Optional

import tiktoken
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI

from ...config import get_settings
from ...schemas.ai import LawReference
from ...utils.pii import sanitize_pii

from ..ai_intent import AiIntentClassifier
from ..ai_response_strategy import ResponseStrategy, ResponseStrategyDecider, SearchQuality
from ..content_safety import ContentSafetyFilter, RiskLevel
from ..disclaimer import DisclaimerManager

from .knowledge_base import LegalKnowledgeBase
from .prompts import LegalAssistantPrompts


settings = get_settings()
logger = logging.getLogger(__name__)


class AILegalAssistant:
    """AI法律咨询助手"""

    llm: ChatOpenAI | None

    def __init__(self):
        api_key = str(getattr(settings, "openai_api_key", "") or "").strip()
        if api_key:
            if "OPENAI_API_KEY" not in os.environ:
                os.environ["OPENAI_API_KEY"] = api_key
        if str(getattr(settings, "openai_base_url", "") or "").strip():
            if "OPENAI_BASE_URL" not in os.environ:
                os.environ["OPENAI_BASE_URL"] = str(
                    getattr(settings, "openai_base_url", "") or "").strip()

        # Only initialize LLM if API key is available
        if api_key:
            self.llm = ChatOpenAI()
            setattr(
                self.llm, "model_name", str(
                    getattr(
                        settings, "ai_model", "") or "").strip())
            setattr(self.llm, "temperature", 0.7)
            mk = getattr(self.llm, "model_kwargs", None)
            if isinstance(mk, dict):
                mk["max_completion_tokens"] = 2000
            else:
                setattr(
                    self.llm, "model_kwargs", {
                        "max_completion_tokens": 2000})
        else:
            self.llm = None

        self.knowledge_base: LegalKnowledgeBase = LegalKnowledgeBase()
        self.knowledge_base.initialize()
        self.safety_filter: ContentSafetyFilter = ContentSafetyFilter()
        self.strategy_decider: ResponseStrategyDecider = ResponseStrategyDecider()
        self.intent_classifier: AiIntentClassifier = AiIntentClassifier()
        self.disclaimer_manager: DisclaimerManager = DisclaimerManager()
        self.conversation_histories: dict[str, list[dict[str, str]]] = {}
        self._last_seen: dict[str, float] = {}
        self._max_sessions: int = 5000
        self._max_messages_per_session: int = 50

    def _encoding_for_model(self, model: str | None):
        m = str(model or "").strip()
        try:
            return tiktoken.encoding_for_model(m)
        except Exception:
            return tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str, *, model: str | None) -> int:
        s = str(text or "")
        if not s:
            return 0
        enc = self._encoding_for_model(model)
        try:
            return int(len(enc.encode(s)))
        except Exception:
            return int(max(0, len(s) // 4))

    def _estimate_cost_usd(
        self,
        *,
        model: str | None,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float | None:
        m = str(model or "").strip().lower()
        if not m:
            return None

        pricing: dict[str, tuple[float, float]] = {
            "gpt-4o-mini": (0.15, 0.60),
            "gpt-4o": (5.00, 15.00),
            "gpt-4.1-mini": (0.15, 0.60),
            "gpt-4.1": (5.00, 15.00),
            "gpt-3.5-turbo": (0.50, 1.50),
        }

        rate = None
        for k, v in pricing.items():
            if m == k or m.startswith(k + "-"):
                rate = v
                break
        if rate is None:
            return None

        in_per_m, out_per_m = rate
        cost = (float(prompt_tokens) / 1_000_000.0) * float(in_per_m) + (
            float(completion_tokens) / 1_000_000.0
        ) * float(out_per_m)
        return float(round(cost, 6))

    def _llm_for_model(self, model: str) -> ChatOpenAI:
        if str(getattr(settings, "openai_api_key", "") or "").strip():
            if "OPENAI_API_KEY" not in os.environ:
                os.environ["OPENAI_API_KEY"] = str(
                    getattr(settings, "openai_api_key", "") or "").strip()
        if str(getattr(settings, "openai_base_url", "") or "").strip():
            if "OPENAI_BASE_URL" not in os.environ:
                os.environ["OPENAI_BASE_URL"] = str(
                    getattr(settings, "openai_base_url", "") or "").strip()

        llm = ChatOpenAI()
        setattr(llm, "model_name", str(model or "").strip())
        setattr(llm, "temperature", 0.7)
        mk = getattr(llm, "model_kwargs", None)
        if isinstance(mk, dict):
            mk["max_completion_tokens"] = 2000
        else:
            setattr(llm, "model_kwargs", {"max_completion_tokens": 2000})
        return llm

    def _model_candidates(self) -> list[str]:
        primary = str(getattr(settings, "ai_model", "") or "").strip()
        fallbacks = cast(
            list[str],
            getattr(
                settings,
                "ai_fallback_models",
                []))
        cleaned_fallbacks = [str(m or "").strip()
                             for m in fallbacks if str(m or "").strip()]
        candidates = [primary] + cleaned_fallbacks
        out: list[str] = []
        seen: set[str] = set()
        for item in candidates:
            if not item:
                continue
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    def _evict_if_needed(self) -> None:
        if len(self.conversation_histories) <= self._max_sessions:
            return

        oldest_session: str | None = None
        oldest_time = float("inf")
        for sid, ts in self._last_seen.items():
            if ts < oldest_time:
                oldest_time = ts
                oldest_session = sid

        if oldest_session is not None:
            _ = self.conversation_histories.pop(oldest_session, None)
            _ = self._last_seen.pop(oldest_session, None)

    def _build_context(
            self, references: list[tuple[str, dict[str, object], float]]) -> str:
        """构建上下文字符串"""
        if not references:
            return "暂无相关法律条文参考，请基于你的法律知识回答。"

        context_parts: list[str] = []
        for i, (content, _metadata, _score) in enumerate(references, 1):
            context_parts.append(f"{i}. {content}")

        return "\n\n".join(context_parts)

    def _parse_references(
            self, references: list[tuple[str, dict[str, object], float]]) -> list[LawReference]:
        """解析法律引用"""
        result: list[LawReference] = []
        for content, metadata, score in references:
            kid: int | None = None
            try:
                raw_kid = metadata.get("knowledge_id")
                if raw_kid is not None and str(raw_kid).strip():
                    kid = int(str(raw_kid).strip())
            except Exception:
                kid = None

            result.append(
                LawReference(
                    content=content,
                    knowledge_id=kid,
                    similarity=float(score),
                    law_name="",
                    article="",
                    relevance=0.0,
                    source=None,
                    source_url=None,
                    source_version=None,
                    source_hash=None,
                    ingest_batch_id=None,
                )
            )
        return result

    def _append_disclaimer(
            self,
            answer: str,
            *,
            risk_level: RiskLevel,
            strategy: ResponseStrategy) -> str:
        disclaimer = self.disclaimer_manager.get_disclaimer(
            risk_level=risk_level, strategy=strategy)
        if disclaimer:
            answer = f"{answer}\n\n---\n{disclaimer}"
        return answer

    def _normalize_history(
            self, history: list[dict[str, str]]) -> list[dict[str, str]]:
        cleaned: list[dict[str, str]] = []
        for msg in history:
            role = str(msg.get("role", "")).strip().lower()
            content = str(msg.get("content", "")).strip()
            if role and content and role in {"user", "assistant", "system"}:
                cleaned.append({"role": role, "content": content})
        return cleaned

    def get_or_create_session(
        self,
        session_id: str | None = None,
        *,
        initial_history: list[dict[str, str]] | None = None,
    ) -> str:
        """获取或创建会话"""
        if session_id:
            sid = str(session_id).strip()
            if sid and sid in self.conversation_histories:
                self._last_seen[sid] = time.time()
                return sid

        new_id = str(session_id).strip() if session_id else str(uuid.uuid4())
        if not new_id:
            new_id = str(uuid.uuid4())

        self.conversation_histories[new_id] = self._normalize_history(
            initial_history or [])
        self._last_seen[new_id] = time.time()
        self._evict_if_needed()
        return new_id

    def clear_session(self, session_id: str) -> None:
        """清空会话"""
        sid = str(session_id).strip()
        if not sid:
            return
        _ = self.conversation_histories.pop(sid, None)
        _ = self._last_seen.pop(sid, None)

    async def chat(
        self,
        message: str,
        session_id: str | None = None,
        *,
        initial_history: list[dict[str, str]] | None = None,
        user_profile: str | None = None,
        prompt_version: str | None = None,
    ) -> tuple[str, str, list[LawReference], dict[str, object]]:
        """与AI助手对话"""
        session_id = self.get_or_create_session(
            session_id, initial_history=initial_history)
        message_for_ai = sanitize_pii(message)
        user_profile_for_ai = sanitize_pii(
            str(user_profile or "").strip()) if user_profile else ""

        intent_result = self.intent_classifier.classify(message_for_ai)
        safety = self.safety_filter.check_input(message_for_ai)

        if safety.risk_level == RiskLevel.BLOCKED:
            strategy = ResponseStrategy.REFUSE_ANSWER
            disclaimer = self.disclaimer_manager.get_disclaimer(
                risk_level=safety.risk_level, strategy=strategy)
            answer = str(safety.suggestion or "很抱歉，我无法回答这类问题。如需帮助，请联系专业机构。")
            answer = self._append_disclaimer(
                answer, risk_level=safety.risk_level, strategy=strategy)
            answer = self.safety_filter.sanitize_output(answer)

            history = self.conversation_histories.get(session_id, [])
            history.append({"role": "user", "content": message_for_ai})
            history.append({"role": "assistant", "content": answer})
            self.conversation_histories[session_id] = history[-self._max_messages_per_session:]
            self._last_seen[session_id] = time.time()
            self._evict_if_needed()

            meta: dict[str, object] = {
                "strategy_used": str(strategy.value),
                "strategy_reason": "内容安全拦截",
                "confidence": "N/A",
                "risk_level": str(safety.risk_level.value),
                "intent": str(intent_result.intent),
                "needs_clarification": bool(intent_result.needs_clarification),
                "clarifying_questions": list(intent_result.clarifying_questions),
                "search_quality": {
                    "total_candidates": 0,
                    "qualified_count": 0,
                    "avg_similarity": 0.0,
                    "confidence": "low",
                },
                "disclaimer": str(disclaimer),
                "model_used": None,
                "fallback_used": False,
                "model_attempts": [],
            }
            return session_id, answer, [], meta

        references, quality = self.knowledge_base.search_with_quality_control(
            message_for_ai, k=5)
        decision = self.strategy_decider.decide(
            message_for_ai, quality, risk_level=safety.risk_level)
        disclaimer = self.disclaimer_manager.get_disclaimer(
            risk_level=safety.risk_level, strategy=decision.strategy)
        context = self._build_context(references)

        history = self.conversation_histories.get(session_id, [])
        model_candidates = self._model_candidates()

        model_used_out: str | None = None
        fallback_used_out: bool = False
        model_attempts_out: list[str] = []
        prompt_tokens = 0
        completion_tokens = 0

        answer: str | None = None

        for model in model_candidates:
            if not model:
                continue
            model_attempts_out.append(model)

            try:
                llm = self._llm_for_model(model)

                user_profile_prompt = f"[用户画像]: {user_profile_for_ai}" if user_profile_for_ai else ""
                system_prompt = LegalAssistantPrompts.get_prompt(
                    prompt_version)
                system_prompt = system_prompt.format(
                    context=context, user_profile_prompt=user_profile_prompt)

                messages: list[BaseMessage] = [
                    SystemMessage(content=system_prompt)]
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

                messages.append(HumanMessage(content=message_for_ai))

                system_msg_for_count = [SystemMessage(content=system_prompt)]
                prompt_tokens = self._count_tokens("".join(
                    [str(m.content) for m in system_msg_for_count + messages[:-1]]), model=model)

                response = await llm.ainvoke(messages)
                answer = cast(str, response.content)

                if not isinstance(answer, str):
                    answer = str(answer) if answer is not None else ""

                completion_tokens = self._count_tokens(answer, model=model)
                model_used_out = model
                break

            except Exception as exc:
                logger.warning("模型 %s 调用失败: %s", model, exc)
                continue

        if answer is None or not answer:
            fallback_model = "gpt-3.5-turbo"
            logger.info("使用 fallback 模型: %s", fallback_model)
            try:
                llm = self._llm_for_model(fallback_model)
                fallback_used_out = True
                if fallback_model not in model_attempts_out:
                    model_attempts_out.append(fallback_model)

                user_profile_prompt = f"[用户画像]: {user_profile_for_ai}" if user_profile_for_ai else ""
                system_prompt = LegalAssistantPrompts.get_prompt(
                    prompt_version)
                system_prompt = system_prompt.format(
                    context=context, user_profile_prompt=user_profile_prompt)

                messages = [SystemMessage(content=system_prompt)]
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
                messages.append(HumanMessage(content=message_for_ai))

                system_msg_for_count = [SystemMessage(content=system_prompt)]
                prompt_tokens = self._count_tokens("".join(
                    [str(m.content) for m in system_msg_for_count + messages[:-1]]), model=fallback_model)

                response = await llm.ainvoke(messages)
                answer = cast(str, response.content)

                if not isinstance(answer, str):
                    answer = str(answer) if answer is not None else ""

                completion_tokens = self._count_tokens(
                    answer, model=fallback_model)
                model_used_out = fallback_model

            except Exception as exc:
                logger.exception("Fallback 模型也失败: %s", exc)
                answer = "很抱歉，AI 服务暂时不可用，请稍后再试或联系客服。"

        answer = self.safety_filter.sanitize_output(answer)
        answer = self._append_disclaimer(
            answer,
            risk_level=safety.risk_level,
            strategy=decision.strategy)

        if history:
            history.append({"role": "user", "content": message_for_ai})
            history.append({"role": "assistant", "content": answer or ""})
            self.conversation_histories[session_id] = history[-self._max_messages_per_session:]
        self._last_seen[session_id] = time.time()
        self._evict_if_needed()

        parsed_references = self._parse_references(references)

        total_tokens = prompt_tokens + completion_tokens
        estimated_cost_usd = self._estimate_cost_usd(
            model=model_used_out,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens)

        meta = {
            "strategy_used": str(
                decision.strategy.value),
            "strategy_reason": str(
                decision.reason),
            "confidence": str(
                decision.confidence),
            "risk_level": str(
                safety.risk_level.value),
            "prompt_version": str(
                prompt_version or "v1"),
            "intent": str(
                intent_result.intent),
            "needs_clarification": bool(
                intent_result.needs_clarification),
            "clarifying_questions": list(
                intent_result.clarifying_questions),
            "search_quality": {
                "total_candidates": quality.total_candidates,
                "qualified_count": quality.qualified_count,
                "avg_similarity": round(
                    float(
                        quality.avg_similarity),
                    4) if quality.avg_similarity else 0.0,
                "confidence": str(
                    decision.confidence),
            },
            "disclaimer": str(disclaimer),
            "model_used": model_used_out,
            "fallback_used": fallback_used_out,
            "model_attempts": model_attempts_out,
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "total_tokens": int(total_tokens),
            "estimated_cost_usd": estimated_cost_usd,
        }

        return session_id, answer or "", parsed_references, meta

    async def chat_stream(
        self,
        message: str,
        session_id: str | None = None,
        *,
        initial_history: list[dict[str, str]] | None = None,
        user_profile: str | None = None,
        prompt_version: str | None = None,
    ) -> AsyncGenerator[tuple[str, str] | tuple[str, str, dict[str, object]], None]:
        """流式对话"""
        # Check if AI service is available
        if not str(getattr(settings, "openai_api_key", "") or "").strip():
            yield ("answer", "很抱歉，AI 服务暂时不可用。")
            yield ("done", "", {"session_id": session_id or "", "strategy_used": "ERROR"})
            return

        session_id = self.get_or_create_session(
            session_id, initial_history=initial_history)
        message_for_ai = sanitize_pii(message)
        user_profile_for_ai = sanitize_pii(
            str(user_profile or "").strip()) if user_profile else ""

        intent_result = self.intent_classifier.classify(message_for_ai)
        safety = self.safety_filter.check_input(message_for_ai)

        if safety.risk_level == RiskLevel.BLOCKED:
            strategy = ResponseStrategy.REFUSE_ANSWER
            disclaimer = self.disclaimer_manager.get_disclaimer(
                risk_level=safety.risk_level, strategy=strategy)
            answer = str(safety.suggestion or "很抱歉，我无法回答这类问题。")
            answer = self._append_disclaimer(
                answer, risk_level=safety.risk_level, strategy=strategy)
            answer = self.safety_filter.sanitize_output(answer)

            yield ("answer", answer, {})
            yield ("done", "", {"session_id": session_id, "strategy_used": str(strategy.value)})
            return

        references, quality = self.knowledge_base.search_with_quality_control(
            message_for_ai, k=5)
        decision = self.strategy_decider.decide(
            message_for_ai, quality, risk_level=safety.risk_level)
        disclaimer = self.disclaimer_manager.get_disclaimer(
            risk_level=safety.risk_level, strategy=decision.strategy)
        context = self._build_context(references)

        history = self.conversation_histories.get(session_id, [])
        model_candidates = self._model_candidates()

        model_used_out: str | None = None
        fallback_used_out: bool = False
        model_attempts_out: list[str] = []
        prompt_tokens = 0
        completion_tokens = 0
        answer_buffer = ""
        full_response = ""

        for model in model_candidates:
            if not model:
                continue
            model_attempts_out.append(model)

            try:
                llm = self._llm_for_model(model)
                user_profile_prompt = f"[用户画像]: {user_profile_for_ai}" if user_profile_for_ai else ""
                system_prompt = LegalAssistantPrompts.get_prompt(
                    prompt_version)
                system_prompt = system_prompt.format(
                    context=context, user_profile_prompt=user_profile_prompt)

                messages: list[BaseMessage] = [
                    SystemMessage(content=system_prompt)]
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
                messages.append(HumanMessage(content=message_for_ai))

                system_msg_for_count = [SystemMessage(content=system_prompt)]
                prompt_tokens = self._count_tokens("".join(
                    [str(m.content) for m in system_msg_for_count + messages[:-1]]), model=model)

                async for chunk in llm.astream(messages):
                    if chunk.content:
                        answer_buffer += str(chunk.content)
                        yield ("answer", answer_buffer)

                full_response = answer_buffer
                completion_tokens = self._count_tokens(
                    full_response, model=model)
                model_used_out = model
                break

            except Exception as exc:
                logger.warning("模型 %s 流式调用失败: %s", model, exc)
                answer_buffer = ""
                continue

        if not full_response:
            fallback_model = "gpt-3.5-turbo"
            logger.info("使用 fallback 模型: %s", fallback_model)
            try:
                llm = self._llm_for_model(fallback_model)
                fallback_used_out = True
                if fallback_model not in model_attempts_out:
                    model_attempts_out.append(fallback_model)

                user_profile_prompt = f"[用户画像]: {user_profile_for_ai}" if user_profile_for_ai else ""
                system_prompt = LegalAssistantPrompts.get_prompt(
                    prompt_version)
                system_prompt = system_prompt.format(
                    context=context, user_profile_prompt=user_profile_prompt)

                messages = [SystemMessage(content=system_prompt)]
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
                messages.append(HumanMessage(content=message_for_ai))

                system_msg_for_count = [SystemMessage(content=system_prompt)]
                prompt_tokens = self._count_tokens("".join(
                    [str(m.content) for m in system_msg_for_count + messages[:-1]]), model=fallback_model)

                async for chunk in llm.astream(messages):
                    if chunk.content:
                        answer_buffer += str(chunk.content)
                        yield ("answer", answer_buffer)

                full_response = answer_buffer
                completion_tokens = self._count_tokens(
                    full_response, model=fallback_model)
                model_used_out = fallback_model

            except Exception as exc:
                logger.exception("Fallback 模型流式也失败: %s", exc)
                yield ("answer", "很抱歉，AI 服务暂时不可用。", {})
                yield ("done", "", {"session_id": session_id, "error": str(exc)})
                return

        full_response = self.safety_filter.sanitize_output(full_response)
        full_response = self._append_disclaimer(
            full_response,
            risk_level=safety.risk_level,
            strategy=decision.strategy)

        if history:
            history.append({"role": "user", "content": message_for_ai})
            history.append({"role": "assistant", "content": full_response})
            self.conversation_histories[session_id] = history[-self._max_messages_per_session:]
        self._last_seen[session_id] = time.time()
        self._evict_if_needed()

        parsed_references = self._parse_references(references)

        total_tokens = prompt_tokens + completion_tokens
        estimated_cost_usd = self._estimate_cost_usd(
            model=model_used_out,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens)

        yield (
            "done",
            "",
            {
                "session_id": session_id,
                "strategy_used": str(decision.strategy.value),
                "strategy_reason": str(decision.reason),
                "confidence": str(decision.confidence),
                "risk_level": str(safety.risk_level.value),
                "prompt_version": str(prompt_version or "v1"),
                "intent": str(intent_result.intent),
                "needs_clarification": bool(intent_result.needs_clarification),
                "model_used": model_used_out,
                "fallback_used": bool(fallback_used_out),
                "model_attempts": list(model_attempts_out),
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(total_tokens),
                "estimated_cost_usd": estimated_cost_usd,
            },
        )


_ai_assistant: AILegalAssistant | None = None


def get_ai_assistant() -> AILegalAssistant:
    """获取AI助手实例（懒加载）"""
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AILegalAssistant()
    return _ai_assistant


# 实例化单例（保持原有使用方式）
ai_assistant = AILegalAssistant()
