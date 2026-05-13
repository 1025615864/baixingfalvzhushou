from __future__ import annotations
import json
import logging
import os
import random
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class NewsAIPipelineService:
    @staticmethod
    def _extract_structured_output(
        text: str,
        highlights_max: int = 5,
        keywords_max: int = 10,
        item_max_chars: int = 200,
    ) -> tuple[str, list[str], list[str]]:
        summary = ""
        highlights: list[str] = []
        keywords: list[str] = []

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return summary, highlights, keywords

        if isinstance(data, dict):
            raw_summary = data.get("summary", "")
            if isinstance(raw_summary, str):
                summary = raw_summary.strip()

            raw_highlights = data.get("highlights", [])
            if isinstance(raw_highlights, list):
                for h in raw_highlights[:highlights_max]:
                    s = str(h).strip()
                    if len(s) > item_max_chars:
                        s = s[:item_max_chars]
                    if s:
                        highlights.append(s)

            raw_keywords = data.get("keywords", [])
            if isinstance(raw_keywords, list):
                for k in raw_keywords[:keywords_max]:
                    s = str(k).strip()
                    if s:
                        keywords.append(s)

        return summary, highlights, keywords

    @staticmethod
    def _build_llm_prompt(article_text: str) -> str:
        return (
            "请对以下新闻文章进行摘要分析，以JSON格式返回结果：\n"
            "字段要求：\n"
            "- summary: 文章摘要（100字以内）\n"
            "- highlights: 要点列表（最多5条，每条50字以内）\n"
            "- keywords: 关键词列表（最多10个）\n\n"
            f"文章内容：\n{article_text}"
        )

    async def _llm_summarize(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        title: str,
        content: str,
        timeout_seconds: float = 30.0,
        summary_max_chars: int = 120,
        highlights_max: int = 5,
        keywords_max: int = 10,
    ) -> str:
        import httpx

        response_format = os.environ.get("NEWS_AI_SUMMARY_LLM_RESPONSE_FORMAT", "text")
        url = f"{base_url.rstrip('/')}/chat/completions"

        prompt = (
            f"请对以下新闻文章进行摘要分析，以JSON格式返回结果：\n"
            f"标题：{title}\n"
            f"内容：{content}\n\n"
            f"字段要求：\n"
            f"- summary: 文章摘要（{summary_max_chars}字以内）\n"
            f"- highlights: 要点列表（最多{highlights_max}条）\n"
            f"- keywords: 关键词列表（最多{keywords_max}个）\n"
        )

        messages = [{"role": "user", "content": prompt}]
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
        }
        if response_format == "json_object":
            body["response_format"] = {"type": "json_object"}
            messages[0]["content"] += "\n\n请以JSON格式返回。"
            body["messages"] = messages

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(url, json=body, headers=headers)
            if resp.status_code == 400 and response_format == "json_object":
                del body["response_format"]
                body["messages"] = [{"role": "user", "content": prompt + "\n\n请以JSON格式返回。"}]
                resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]

    async def summarize(self, article_text: str, **kwargs) -> dict[str, Any]:
        response_format = os.environ.get("NEWS_AI_SUMMARY_LLM_RESPONSE_FORMAT", "text")
        prompt = self._build_llm_prompt(article_text)

        try:
            from app.config import get_settings
            settings = get_settings()
            api_key = getattr(settings, "openai_api_key", "") or ""
            if not api_key:
                return {"summary": "", "highlights": [], "keywords": []}

            import httpx
            base_url = getattr(settings, "openai_api_base", "https://api.openai.com/v1") or "https://api.openai.com/v1"
            url = f"{base_url.rstrip('/')}/chat/completions"
            model = getattr(settings, "openai_model", "gpt-4o-mini") or "gpt-4o-mini"

            messages = [{"role": "user", "content": prompt}]
            body: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
            }
            if response_format == "json_object":
                body["response_format"] = {"type": "json_object"}
                messages[0]["content"] += "\n\n请以JSON格式返回。"
                body["messages"] = messages

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"]
            summary, highlights, keywords = self._extract_structured_output(content)
            return {"summary": summary, "highlights": highlights, "keywords": keywords}
        except Exception as e:
            logger.error(f"News AI summarize error: {e}")
            return {"summary": "", "highlights": [], "keywords": []}

    def get_summary_llm_providers(
        self,
        settings: Any,
        *,
        env_overrides: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        providers_json_str = (env_overrides or {}).get(
            "NEWS_AI_SUMMARY_LLM_PROVIDERS_JSON"
        ) or os.environ.get("NEWS_AI_SUMMARY_LLM_PROVIDERS_JSON", "[]")

        try:
            providers: list[dict[str, Any]] = json.loads(providers_json_str)
        except (json.JSONDecodeError, TypeError):
            providers = []

        resolved: list[dict[str, Any]] = []
        for p in providers:
            entry = dict(p)
            name = entry.get("name", "")
            if not entry.get("base_url"):
                if name == "openai":
                    entry["base_url"] = getattr(settings, "openai_api_base", "") or os.environ.get("OPENAI_BASE_URL", "")
                elif name == "azure-openai":
                    entry["base_url"] = getattr(settings, "azure_openai_base_url", "") or os.environ.get("AZURE_OPENAI_BASE_URL", "")
            if not entry.get("api_key"):
                if name == "openai":
                    entry["api_key"] = getattr(settings, "openai_api_key", "") or os.environ.get("OPENAI_API_KEY", "")
                elif name == "azure-openai":
                    entry["api_key"] = getattr(settings, "azure_openai_api_key", "") or os.environ.get("AZURE_OPENAI_API_KEY", "")
            if not entry.get("model"):
                if name == "openai":
                    entry["model"] = getattr(settings, "openai_model", "") or os.environ.get("AI_MODEL", "")
                elif name == "azure-openai":
                    entry["model"] = getattr(settings, "azure_openai_model", "") or os.environ.get("AZURE_OPENAI_MODEL", "")
            resolved.append(entry)

        return resolved

    async def _make_summary(
        self,
        db: object,
        news: object,
        *,
        env_overrides: dict | None = None,
        force_generate: bool = False,
    ) -> tuple[str, bool, list[str], list[str]]:
        llm_enabled = os.environ.get("NEWS_AI_SUMMARY_LLM_ENABLED", "0") == "1"

        if not llm_enabled:
            result = await self.summarize(getattr(news, "content", "") or "")
            return result.get("summary", ""), False, result.get("highlights", []), result.get("keywords", [])

        from app.config import get_settings
        settings = get_settings()

        providers = self.get_summary_llm_providers(settings, env_overrides=env_overrides)

        strategy = (env_overrides or {}).get(
            "NEWS_AI_SUMMARY_LLM_PROVIDER_STRATEGY"
        ) or os.environ.get("NEWS_AI_SUMMARY_LLM_PROVIDER_STRATEGY", "random")

        if strategy == "priority":
            providers_sorted = sorted(providers, key=lambda p: int(p.get("priority", 999)))
        else:
            providers_sorted = list(providers)
            random.shuffle(providers_sorted)

        title = getattr(news, "title", "") or ""
        content = getattr(news, "content", "") or ""

        for provider in providers_sorted:
            api_key = provider.get("api_key", "")
            base_url = provider.get("base_url", "")
            model = provider.get("model", "")
            if not api_key:
                api_key = getattr(settings, "openai_api_key", "") or os.environ.get("OPENAI_API_KEY", "")
            if not base_url:
                base_url = getattr(settings, "openai_api_base", "") or os.environ.get("OPENAI_BASE_URL", "")
            if not model:
                model = getattr(settings, "openai_model", "") or os.environ.get("AI_MODEL", "")

            try:
                raw = await self._llm_summarize(
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    title=title,
                    content=content,
                )
                summary, highlights, keywords = self._extract_structured_output(raw)
                return summary, True, highlights, keywords
            except Exception:
                logger.warning(f"Provider {provider.get('name', 'unknown')} failed, trying next")
                continue

        result = await self.summarize(content)
        return result.get("summary", ""), False, result.get("highlights", []), result.get("keywords", [])

    def _make_risk(self, news: object) -> tuple[str, Optional[str]]:
        return "safe", None

    async def _find_duplicate_of(self, db: object, news: object) -> Optional[object]:
        return None

    @staticmethod
    async def load_system_config_overrides(db: Any) -> dict[str, str]:
        from sqlalchemy import select
        from app.models.system import SystemConfig

        result = await db.execute(select(SystemConfig).where(SystemConfig.category == "news_ai"))
        rows = result.scalars().all()

        overrides: dict[str, str] = {}
        env_suffix = os.environ.get("APP_ENV", "")

        for row in rows:
            key = str(row.key)
            value = str(row.value) if row.value is not None else ""
            overrides[key] = value

        if env_suffix:
            suffix_key_map: dict[str, str] = {}
            for row in rows:
                key = str(row.key)
                suffix = f"_{env_suffix.upper()}"
                if key.endswith(suffix):
                    base_key = key[: -len(suffix)]
                    suffix_key_map[base_key] = str(row.value) if row.value is not None else ""

            for base_key, val in suffix_key_map.items():
                overrides[base_key] = val

        return overrides

    async def run_once(self, db: Any) -> dict[str, int]:
        import os as _os
        from sqlalchemy import select
        from app.models.news import News
        from app.models.news_ai import NewsAIAnnotation

        summary_enabled = _os.environ.get("NEWS_AI_SUMMARY_ENABLED", "0") == "1"
        writeback_enabled = _os.environ.get("NEWS_AI_SUMMARY_WRITEBACK_ENABLED", "0") == "1"
        review_policy_enabled = _os.environ.get("NEWS_REVIEW_POLICY_ENABLED", "0") == "1"

        query = select(News).where(News.is_published == True)
        if not summary_enabled:
            query = select(News)

        result = await db.execute(query)
        news_list = result.scalars().all()

        processed = 0
        created = 0
        errors = 0

        for news in news_list:
            try:
                ann_result = await db.execute(
                    select(NewsAIAnnotation).where(NewsAIAnnotation.news_id == news.id)
                )
                annotation = ann_result.scalar_one_or_none()

                summary, is_llm, highlights, keywords = await self._make_summary(db, news)
                risk_level, risk_reason = self._make_risk(news)
                duplicate = await self._find_duplicate_of(db, news)

                if annotation is None:
                    annotation = NewsAIAnnotation(
                        news_id=news.id,
                        summary=summary,
                        highlights=json.dumps(highlights, ensure_ascii=False) if highlights else None,
                        keywords=json.dumps(keywords, ensure_ascii=False) if keywords else None,
                        processed_at=datetime.now(timezone.utc),
                    )
                    db.add(annotation)
                    created += 1
                else:
                    annotation.summary = summary
                    annotation.highlights = json.dumps(highlights, ensure_ascii=False) if highlights else None
                    annotation.keywords = json.dumps(keywords, ensure_ascii=False) if keywords else None
                    annotation.processed_at = datetime.now(timezone.utc)

                if writeback_enabled and summary:
                    news.summary = summary

                if review_policy_enabled and getattr(news, "review_status", None) == "pending":
                    if risk_level == "safe":
                        news.review_status = "approved"
                        news.reviewed_at = datetime.now(timezone.utc)
                        news.review_reason = risk_reason or ""

                processed += 1
            except Exception as e:
                logger.error(f"Error processing news {getattr(news, 'id', '?')}: {e}")
                errors += 1

        await db.commit()
        return {"processed": processed, "created": created, "errors": errors}


news_ai_pipeline_service = NewsAIPipelineService()
