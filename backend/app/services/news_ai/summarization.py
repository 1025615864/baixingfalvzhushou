"""新闻AI摘要生成服务

提供新闻AI摘要、高亮、关键词提取等功能
"""
from .core import NewsAIPipelineService, _risk_from_filter
import asyncio
import base64
import hashlib
import json
import logging
import os
import random
import re
from datetime import datetime
from typing import Any, Literal, cast
from typing_extensions import TypedDict

import httpx
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...models.news import News
from ...models.news_ai import NewsAIAnnotation
from ...models.system import SystemConfig
from ...services.critical_event_reporter import critical_event_reporter
from ...utils.content_filter import content_filter
from ...utils.pii import sanitize_pii


logger = logging.getLogger(__name__)


def _truncate(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    if len(v) <= int(max_len):
        return v
    return v[: int(max_len)]


def _current_env_token() -> str | None:
    raw = str(os.getenv("APP_ENV") or os.getenv("ENV")
              or os.getenv("ENVIRONMENT") or "").strip()
    if not raw:
        return None
    v = raw.strip().lower()
    if v in {"prod", "production"}:
        return "PROD"
    if v in {"stag", "staging"}:
        return "STAGING"
    if v in {"dev", "development"}:
        return "DEV"
    if v in {"test", "testing"}:
        return "TEST"
    v2 = re.sub(r"[^a-z0-9]+", "_", v).strip("_")
    return v2.upper() if v2 else None


def _retry_status_codes() -> set[int]:
    default_codes = {408, 429, 500, 502, 503, 504}
    raw = str(
        os.getenv(
            "NEWS_AI_SUMMARY_LLM_RETRY_STATUS_CODES",
            "") or "").strip()
    if not raw:
        return default_codes
    codes: set[int] = set()
    for chunk in raw.split(","):
        part = chunk.strip()
        if not part:
            continue
        try:
            codes.add(int(part))
        except ValueError:
            continue
    return codes or default_codes


def _classify_llm_exception(exc: Exception) -> tuple[str, int | None]:
    if isinstance(exc, httpx.TimeoutException):
        return "NEWS_AI_PROVIDER_TIMEOUT", None
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = int(
            exc.response.status_code) if exc.response is not None else None
        if status_code == 429:
            return "NEWS_AI_PROVIDER_RATE_LIMIT", status_code
        if status_code is not None and status_code >= 500:
            return "NEWS_AI_PROVIDER_UPSTREAM", status_code
        if status_code is not None and status_code >= 400:
            return "NEWS_AI_PROVIDER_BAD_RESPONSE", status_code
        return "NEWS_AI_PROVIDER_HTTP_ERROR", status_code
    if isinstance(exc, httpx.RequestError):
        return "NEWS_AI_PROVIDER_NETWORK", None
    return "NEWS_AI_PROVIDER_ERROR", None


def _should_retry_llm_exception(
        exc: Exception, retry_statuses: set[int]) -> bool:
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.RequestError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = int(
            exc.response.status_code) if exc.response is not None else None
        return bool(
            status_code in retry_statuses) if status_code is not None else False
    return False


def _is_response_format_unsupported(exc: httpx.HTTPStatusError) -> bool:
    try:
        status_code = int(
            exc.response.status_code) if exc.response is not None else None
    except Exception:
        status_code = None
    if status_code != 400:
        return False
    response_text = ""
    if exc.response is not None:
        try:
            response_text = str(exc.response.text or "")
        except Exception:
            response_text = ""
    if not response_text:
        return True
    return "response_format" in response_text.lower()


class _NewsSummaryLLMProvider(TypedDict, total=False):
    name: str
    base_url: str
    api_key: str
    model: str
    response_format: str
    auth_type: Literal["bearer", "header"]
    auth_header_name: str
    auth_prefix: str
    chat_completions_path: str
    weight: int
    priority: int


class NewsAISummarizationService:
    """新闻AI摘要生成服务"""

    @staticmethod
    def _bool_env(name: str, default: bool = False) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return bool(default)
        v = str(raw).strip().lower()
        if not v:
            return bool(default)
        return v in {"1", "true", "yes", "y", "on"}

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, object] | None:
        t = str(text or "").strip()
        if not t:
            return None

        if t.startswith("```"):
            t = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", t)
            t = re.sub(r"\n```$", "", t).strip()

        try:
            parsed: object = cast(object, json.loads(t))
            if isinstance(parsed, dict):
                parsed_dict = cast(dict[object, object], parsed)
                return {str(k): v for k, v in parsed_dict.items()}
        except Exception:
            pass

        start = t.find("{")
        end = t.rfind("}")
        if start >= 0 and end > start:
            snippet = t[start: end + 1]
            try:
                parsed2: object = cast(object, json.loads(snippet))
                if isinstance(parsed2, dict):
                    parsed2_dict = cast(dict[object, object], parsed2)
                    return {str(k): v for k, v in parsed2_dict.items()}
            except Exception:
                return None

        return None

    @staticmethod
    def _extract_structured_output(
        text: str,
        *,
        highlights_max: int,
        keywords_max: int,
        item_max_chars: int,
    ) -> tuple[str | None, list[str], list[str]]:
        t = str(text or "").strip()
        if not t:
            return None, [], []

        obj = NewsAISummarizationService._extract_json_object(t)
        if obj is None:
            return t, [], []

        summary_raw = obj.get("summary")
        summary = summary_raw.strip() if isinstance(
            summary_raw, str) and summary_raw.strip() else None

        def _as_list(value: object, max_items: int) -> list[str]:
            if not isinstance(value, list):
                return []

            out: list[str] = []
            items = cast(list[object], value)
            for x in items:
                if len(out) >= int(max_items):
                    break
                s = str(x or "").strip()
                s = _truncate(s, int(item_max_chars)) or ""
                if s:
                    out.append(s)
            return out

        highlights = _as_list(obj.get("highlights"), int(highlights_max))
        keywords = _as_list(obj.get("keywords"), int(keywords_max))
        return summary, highlights, keywords

    def _get_summary_llm_providers(
        self,
        settings: object,
        *,
        env_overrides: dict[str, str] | None = None,
    ) -> list[_NewsSummaryLLMProvider]:
        def _apply_defaults(
                providers: list[_NewsSummaryLLMProvider]) -> list[_NewsSummaryLLMProvider]:
            if not providers:
                return []
            openai_api_key = str(
                getattr(
                    settings,
                    "openai_api_key",
                    "") or os.getenv(
                    "OPENAI_API_KEY",
                    "")).strip()
            openai_base_url = str(
                getattr(
                    settings,
                    "openai_base_url",
                    "") or os.getenv(
                    "OPENAI_BASE_URL",
                    "")
            ).strip()
            openai_model = str(
                getattr(
                    settings,
                    "ai_model",
                    "") or os.getenv(
                    "AI_MODEL",
                    "")).strip()

            azure_api_key = str(
                os.getenv(
                    "AZURE_OPENAI_API_KEY",
                    "") or "").strip()
            azure_base_url = str(
                os.getenv(
                    "AZURE_OPENAI_BASE_URL",
                    "") or "").strip()
            azure_model = str(
                os.getenv(
                    "AZURE_OPENAI_MODEL",
                    "") or "").strip()

            def _set_if_missing(target: _NewsSummaryLLMProvider,
                                key: str, value: str) -> None:
                if not value:
                    return
                if not str(target.get(key, "") or "").strip():
                    target[key] = value

            for provider in providers:
                name = str(provider.get("name", "") or "").strip().lower()
                if name in {"azure-openai", "azure"}:
                    _set_if_missing(provider, "api_key", azure_api_key)
                    _set_if_missing(provider, "base_url", azure_base_url)
                    _set_if_missing(provider, "model", azure_model)
                _set_if_missing(provider, "api_key", openai_api_key)
                _set_if_missing(provider, "base_url", openai_base_url)
                _set_if_missing(provider, "model", openai_model)

            return providers

        def _coerce_providers(obj: object) -> list[_NewsSummaryLLMProvider]:
            if not isinstance(obj, list):
                return []
            providers: list[_NewsSummaryLLMProvider] = []
            for item in cast(list[object], obj):
                if isinstance(item, dict):
                    providers.append(cast(_NewsSummaryLLMProvider, item))
            return providers

        override_json = (env_overrides or {}).get(
            "NEWS_AI_SUMMARY_LLM_PROVIDERS_JSON")
        override_b64 = (env_overrides or {}).get(
            "NEWS_AI_SUMMARY_LLM_PROVIDERS_B64")
        providers_from_overrides = bool(
            (override_json is not None and str(override_json).strip())
            or (override_b64 is not None and str(override_b64).strip())
        )

        env_token = _current_env_token()
        raw_json_env = (
            str(os.getenv(
                f"NEWS_AI_SUMMARY_LLM_PROVIDERS_JSON_{env_token}", "") or "").strip()
            if env_token
            else ""
        )
        raw_b64_env = (
            str(os.getenv(
                f"NEWS_AI_SUMMARY_LLM_PROVIDERS_B64_{env_token}", "") or "").strip()
            if env_token
            else ""
        )

        if providers_from_overrides:
            if override_json:
                try:
                    parsed = cast(list[object], json.loads(override_json))
                    providers = _coerce_providers(parsed)
                    if providers:
                        return _apply_defaults(providers)
                except Exception:
                    pass
            if override_b64:
                try:
                    decoded = base64.b64decode(override_b64).decode("utf-8")
                    parsed = cast(list[object], json.loads(decoded))
                    providers = _coerce_providers(parsed)
                    if providers:
                        return _apply_defaults(providers)
                except Exception:
                    pass

        if raw_json_env:
            try:
                parsed = cast(list[object], json.loads(raw_json_env))
                providers = _coerce_providers(parsed)
                if providers:
                    return _apply_defaults(providers)
            except Exception:
                pass

        if raw_b64_env:
            try:
                decoded = base64.b64decode(raw_b64_env).decode("utf-8")
                parsed = cast(list[object], json.loads(decoded))
                providers = _coerce_providers(parsed)
                if providers:
                    return _apply_defaults(providers)
            except Exception:
                pass

        default_json = str(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_PROVIDERS_JSON",
                "") or "").strip()
        default_b64 = str(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_PROVIDERS_B64",
                "") or "").strip()

        if default_json:
            try:
                parsed = cast(list[object], json.loads(default_json))
                providers = _coerce_providers(parsed)
                if providers:
                    return _apply_defaults(providers)
            except Exception:
                pass

        if default_b64:
            try:
                decoded = base64.b64decode(default_b64).decode("utf-8")
                parsed = cast(list[object], json.loads(decoded))
                providers = _coerce_providers(parsed)
                if providers:
                    return _apply_defaults(providers)
            except Exception:
                pass

        return []

    def _order_summary_llm_providers(
        self, providers: list[_NewsSummaryLLMProvider], *, strategy: str = "priority"
    ) -> list[_NewsSummaryLLMProvider]:
        if strategy == "random":
            shuffled = list(providers)
            random.shuffle(shuffled)
            return shuffled
        elif strategy == "weight":
            return sorted(providers, key=lambda p: int(
                p.get("weight", 0) or 0), reverse=True)
        else:
            return sorted(providers, key=lambda p: int(
                p.get("priority", 0) or 0))

    def _make_summary_local(self, news: News) -> str | None:
        return _truncate(getattr(news, "summary", None), 500)

    def _make_local_highlights_keywords(
        self,
        *,
        title: str,
        content: str,
        highlights_max: int,
        keywords_max: int,
        item_max_chars: int,
    ) -> tuple[list[str], list[str]]:
        title_kw = re.split(r"[,，\s]+", title.strip())
        title_kw = [re.sub(r"[^\w\u4e00-\u9fff]+", "", k).strip()
                    for k in title_kw if k and len(k) >= 2]
        title_kw = list(dict.fromkeys(title_kw))[:3]

        stop_words = {
            "的",
            "了",
            "是",
            "在",
            "和",
            "与",
            "或",
            "等",
            "为",
            "于",
            "对",
            "从",
            "到",
            "把",
            "被",
            "让",
            "给"}
        content_kw = re.findall(r"[\w\u4e00-\u9fff]{2,10}", content)
        content_kw = [
            k for k in content_kw if k not in stop_words and k not in title_kw]
        content_kw = random.sample(content_kw, min(len(content_kw), 5))

        combined_kw = list(
            dict.fromkeys(
                title_kw +
                content_kw))[
            :int(keywords_max)]
        keywords = [re.sub(r"[^\w\u4e00-\u9fff]+", "", k)
                    [: int(item_max_chars)] for k in combined_kw]

        highlights = [title] if title else []

        return highlights, keywords

    async def _llm_summarize(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        title: str,
        content: str,
        timeout_seconds: float,
        summary_max_chars: int,
        highlights_max: int,
        keywords_max: int,
        response_format: str | None,
        auth_header_name: str | None,
        auth_prefix: str | None,
        chat_completions_path: str | None,
    ) -> str:
        item_max_chars = int(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_ITEM_MAX_CHARS",
                "40").strip() or "40")
        retry_max = max(
            0, int(
                os.getenv(
                    "NEWS_AI_SUMMARY_LLM_RETRY_MAX", "1").strip() or "1"))
        backoff_seconds = float(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_RETRY_BACKOFF_SECONDS",
                "0.5").strip() or "0.5"
        )
        backoff_seconds = max(0.0, float(backoff_seconds))
        retry_statuses = _retry_status_codes()

        prompt = f"""请对以下新闻生成摘要、高亮和关键词：

标题：{title}

内容：{content}

请用JSON格式输出，包含：
- summary: 简要摘要（{summary_max_chars}字以内）
- highlights: {highlights_max}个高亮句子
- keywords: {keywords_max}个关键词

JSON格式："""

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if auth_header_name and auth_prefix:
            headers[auth_header_name] = f"{auth_prefix}{api_key}"
        elif auth_header_name:
            headers[auth_header_name] = api_key
        else:
            headers["Authorization"] = f"Bearer {api_key}"

        chat_path = chat_completions_path or "/v1/chat/completions"
        if not base_url.endswith("/"):
            base_url += "/"
        url = f"{base_url}{chat_path.lstrip('/')}"

        remaining_attempts = max(1, int(retry_max) + 1)
        use_response_format = response_format

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            while True:
                payload: dict[str, object] = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                }

                if use_response_format == "json_object":
                    payload["response_format"] = {"type": "json_object"}

                try:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    text = data.get(
                        "choices", [
                            {}])[0].get(
                        "message", {}).get(
                        "content", "")
                    return str(text)
                except httpx.HTTPStatusError as exc:
                    if use_response_format and _is_response_format_unsupported(
                            exc):
                        use_response_format = None
                        continue
                    if remaining_attempts <= 1 or not _should_retry_llm_exception(
                            exc, retry_statuses):
                        raise
                    remaining_attempts -= 1
                    if backoff_seconds:
                        await asyncio.sleep(backoff_seconds)
                    continue
                except Exception as exc:
                    if remaining_attempts <= 1 or not _should_retry_llm_exception(
                            exc, retry_statuses):
                        raise
                    remaining_attempts -= 1
                    if backoff_seconds:
                        await asyncio.sleep(backoff_seconds)
                    continue

    async def process_news_ai_annotation(
        self,
        db: AsyncSession,
        news: News,
        news_id: int,
        annotation: NewsAIAnnotation,
    ) -> NewsAIAnnotation:
        """处理单条新闻的AI标注"""
        overrides = await NewsAIPipelineService.load_system_config_overrides(db) if hasattr(NewsAIPipelineService, "load_system_config_overrides") else {}
        settings = get_settings()

        try:
            content = str(getattr(news, "content", "") or "").strip()
            title = str(getattr(news, "title", "") or "").strip()
            text_for_filter = f"{title}\n{content}"
            filter_passed, filter_reason, _ = content_filter.check_content(
                text_for_filter)
            risk_level = _risk_from_filter(filter_passed, filter_reason)
            sanitized_content = sanitize_pii(content)

            # Call _make_summary on NewsAIPipelineService to support test
            # monkeypatching (instance or class level)
            from .core import get_news_ai_pipeline_service
            pipeline_service = get_news_ai_pipeline_service()
            summary_func = getattr(pipeline_service, "_make_summary")
            if getattr(summary_func, "__self__", None) is None and hasattr(summary_func, "__get__"):
                summary_func = summary_func.__get__(pipeline_service, type(pipeline_service))
            try:
                summary, from_llm, highlights, keywords = await summary_func(
                    news, env_overrides=overrides, force_generate=False
                )
            except TypeError:
                summary, from_llm, highlights, keywords = await summary_func(
                    news, env_overrides=overrides
                )

            duplicate_func = getattr(pipeline_service, "_find_duplicate_of")
            if getattr(duplicate_func, "__self__", None) is None and hasattr(duplicate_func, "__get__"):
                duplicate_func = duplicate_func.__get__(pipeline_service, type(pipeline_service))
            duplicate_of = await duplicate_func(db, news)

            annotation.summary = summary
            annotation.highlights = json.dumps(
                highlights, ensure_ascii=False) if highlights else None
            annotation.keywords = json.dumps(
                keywords, ensure_ascii=False) if keywords else None
            annotation.risk_level = risk_level
            annotation.sensitive_words = filter_reason
            annotation.duplicate_of_news_id = duplicate_of
            annotation.processed_at = datetime.now()
            db.add(annotation)

            critical_event_reporter.fire_and_forget(
                event="news_ai_completed",
                data={
                    "news_id": news_id,
                    "risk_level": risk_level,
                    "has_summary": bool(summary),
                    "keywords_count": len(keywords) if keywords else 0,
                    "from_llm": from_llm,
                    "duplicate_of": duplicate_of,
                },
            )

        except Exception as exc:
            logger.exception("process_news_ai_annotation failed news_id=%s", str(news_id))
            error_code, _ = _classify_llm_exception(exc)
            annotation.retry_count = (annotation.retry_count or 0) + 1
            annotation.last_error = (
                f"{error_code}: {type(exc).__name__}: {str(exc)[:200]}"
            )
            annotation.last_error_at = datetime.now()
            db.add(annotation)

            critical_event_reporter.fire_and_forget(
                event="news_ai_failed",
                data={
                    "news_id": news_id,
                    "error": str(exc)[
                        :500],
                    "error_code": error_code},
            )

        return annotation

    async def _make_summary(
        self,
        news: News,
        *,
        env_overrides: dict[str, str] | None = None,
        force_generate: bool = False,
    ) -> tuple[str | None, bool, list[str], list[str]]:
        if not bool(force_generate):
            s = _truncate(getattr(news, "summary", None), 500)
            if s:
                return s, False, [], []

        settings = get_settings()

        def _env(name: str, default: str = "") -> str:
            if env_overrides is not None:
                v = env_overrides.get(name)
                if v is not None and str(v).strip():
                    return str(v).strip()
            raw = os.getenv(name)
            if raw is None:
                return default
            return str(raw)

        def _bool(name: str, default: bool = False) -> bool:
            raw = _env(name, "")
            if not raw.strip():
                return bool(default)
            v = raw.strip().lower()
            return v in {"1", "true", "yes", "y", "on"}

        providers = self._get_summary_llm_providers(
            settings, env_overrides=env_overrides)

        mock_generated = str(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_MOCK_RESPONSE",
                "") or "").strip()
        mock_b64_raw = str(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_MOCK_RESPONSE_B64",
                "") or "").strip()
        if not mock_generated and mock_b64_raw:
            try:
                mock_generated = base64.b64decode(
                    mock_b64_raw).decode("utf-8").strip()
            except Exception:
                mock_generated = ""

        highlights_max = int(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_HIGHLIGHTS_MAX",
                "3").strip() or "3")
        keywords_max = int(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_KEYWORDS_MAX",
                "5").strip() or "5")
        item_max_chars = int(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_ITEM_MAX_CHARS",
                "40").strip() or "40")

        if (not mock_generated) and (
                not _bool("NEWS_AI_SUMMARY_LLM_ENABLED", False)):
            local_summary = self._make_summary_local(news)
            highlights, keywords = self._make_local_highlights_keywords(
                title=str(getattr(news, "title", "") or ""),
                content=str(getattr(news, "content", "") or ""),
                highlights_max=int(highlights_max),
                keywords_max=int(keywords_max),
                item_max_chars=int(item_max_chars),
            )
            return local_summary, False, highlights, keywords

        if (not mock_generated) and (not providers):
            local_summary = self._make_summary_local(news)
            highlights, keywords = self._make_local_highlights_keywords(
                title=str(getattr(news, "title", "") or ""),
                content=str(getattr(news, "content", "") or ""),
                highlights_max=int(highlights_max),
                keywords_max=int(keywords_max),
                item_max_chars=int(item_max_chars),
            )
            return local_summary, False, highlights, keywords

        title = str(getattr(news, "title", "") or "").strip()
        content = str(getattr(news, "content", "") or "").strip()
        if not content and title:
            highlights, keywords = self._make_local_highlights_keywords(
                title=title,
                content="",
                highlights_max=int(highlights_max),
                keywords_max=int(keywords_max),
                item_max_chars=int(item_max_chars),
            )
            return _truncate(title, 500), False, highlights, keywords

        max_chars = int(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_MAX_CHARS",
                "4000").strip() or "4000")
        summary_max_chars = int(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_SUMMARY_MAX_CHARS",
                "120").strip() or "120")
        content_for_prompt = content.replace("\n", " ")
        if len(content_for_prompt) > int(max_chars):
            content_for_prompt = content_for_prompt[: int(max_chars)]

        timeout_seconds = float(
            os.getenv(
                "NEWS_AI_SUMMARY_LLM_TIMEOUT_SECONDS",
                "20").strip() or "20")
        generated = None
        last_exc: Exception | None = None
        last_error_code: str | None = None
        last_error_status: int | None = None

        try:
            if mock_generated:
                generated = mock_generated
            else:
                strategy = _env(
                    "NEWS_AI_SUMMARY_LLM_PROVIDER_STRATEGY",
                    "priority").strip()
                ordered = self._order_summary_llm_providers(
                    providers, strategy=strategy)
                from .core import get_news_ai_pipeline_service
                pipeline_service = get_news_ai_pipeline_service()

                for p in ordered:
                    p_api_key = str(p.get("api_key", "") or "").strip()
                    p_base_url = str(p.get("base_url", "") or "").strip()
                    p_model = str(
                        p.get(
                            "model",
                            "") or "").strip() or "gpt-4o-mini"

                    if (not p_base_url) or (not p_api_key):
                        continue

                    auth_type = str(p.get("auth_type", "bearer")
                                    or "bearer").strip().lower()
                    auth_header_name: str | None = None
                    auth_prefix: str | None = None
                    if auth_type == "header":
                        auth_header_name = str(
                            p.get(
                                "auth_header_name",
                                "") or "").strip() or "api-key"
                        auth_prefix = str(p.get("auth_prefix", "") or "")

                    chat_path_raw = str(
                        p.get(
                            "chat_completions_path",
                            "") or "").strip()
                    chat_path = chat_path_raw if chat_path_raw else None

                    rf_raw = str(p.get("response_format", "") or "").strip()
                    rf_env = _env(
                        "NEWS_AI_SUMMARY_LLM_RESPONSE_FORMAT", "").strip()
                    rf = rf_raw if rf_raw else (rf_env or None)

                    try:
                        generated = await pipeline_service._llm_summarize(
                            api_key=p_api_key,
                            base_url=p_base_url,
                            model=p_model,
                            title=title,
                            content=content_for_prompt,
                            timeout_seconds=timeout_seconds,
                            summary_max_chars=int(summary_max_chars),
                            highlights_max=int(highlights_max),
                            keywords_max=int(keywords_max),
                            response_format=rf,
                            auth_header_name=auth_header_name,
                            auth_prefix=auth_prefix,
                            chat_completions_path=chat_path,
                        )
                        if generated:
                            break
                    except Exception as e:
                        last_exc = e
                        last_error_code, last_error_status = _classify_llm_exception(
                            e)
                        logger.info(
                            "news_ai_summary_llm provider_failed name=%s base_url=%s error_code=%s status=%s", str(
                                p.get(
                                    "name", "") or ""), p_base_url, str(
                                last_error_code or ""), str(
                                last_error_status or ""), exc_info=True, )
                        continue

                if (not generated) and (last_exc is not None):
                    raise last_exc
        except Exception as exc:
            logger.exception(
                "news_ai_summary_llm failed news_id=%s", int(
                    getattr(
                        news, "id", 0) or 0))
            if last_error_code:
                critical_event_reporter.fire_and_forget(
                    event="news_ai_summary_llm_failed",
                    data={
                        "news_id": int(getattr(news, "id", 0) or 0),
                        "error": str(exc)[:500],
                        "error_code": last_error_code,
                        "status_code": last_error_status,
                    },
                )
            local_summary = self._make_summary_local(news)
            highlights, keywords = self._make_local_highlights_keywords(
                title=title,
                content=content,
                highlights_max=int(highlights_max),
                keywords_max=int(keywords_max),
                item_max_chars=int(item_max_chars),
            )
            return local_summary, False, highlights, keywords

        summary, highlights, keywords = self._extract_structured_output(
            str(generated or ""),
            highlights_max=int(highlights_max),
            keywords_max=int(keywords_max),
            item_max_chars=int(item_max_chars),
        )
        summary = _truncate(summary, int(summary_max_chars))
        if (not highlights) or (not keywords):
            local_highlights, local_keywords = self._make_local_highlights_keywords(
                title=title,
                content=content,
                highlights_max=int(highlights_max),
                keywords_max=int(keywords_max),
                item_max_chars=int(item_max_chars),
            )
            if not highlights:
                highlights = local_highlights
            if not keywords:
                keywords = local_keywords
        if summary:
            return _truncate(summary, 500), True, highlights, keywords
        local_summary = self._make_summary_local(news)
        local_highlights, local_keywords = self._make_local_highlights_keywords(
            title=title,
            content=content,
            highlights_max=int(highlights_max),
            keywords_max=int(keywords_max),
            item_max_chars=int(item_max_chars),
        )
        return local_summary, False, local_highlights, local_keywords


# 导入 NewsAIPipelineService 用于引用

# 单例
news_ai_summarization_service = NewsAISummarizationService()
