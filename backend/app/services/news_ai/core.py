"""新闻AI流水线服务核心

提供新闻AI处理的主体服务
"""
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
from ...utils.helpers import _truncate
from ...utils.pii import sanitize_pii


logger = logging.getLogger(__name__)


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


def _normalize_title(title: str) -> str:
    t = str(title or "").strip().lower()
    t = " ".join(t.split())
    return t


def _fingerprint(news: News) -> str:
    base = (
        f"{_normalize_title(news.title)}|"
        f"{str(getattr(news, 'source_site', '') or '').strip().lower()}"
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _risk_from_filter(passed: bool, reason: str) -> str:
    r = str(reason or "").strip()
    if passed:
        return "safe"
    if r == "内容疑似广告":
        return "warning"
    if r == "内容包含敏感词汇":
        return "danger"
    return "warning"


class NewsAIPipelineService:
    """新闻AI流水线服务"""

    def __init__(self) -> None:
        self._rr_cursor: int = 0

    @staticmethod
    async def load_system_config_overrides(db: AsyncSession) -> dict[str, str]:
        """加载系统配置覆盖"""
        result = await db.execute(select(SystemConfig))
        configs = result.scalars().all()
        env_token = _current_env_token()
        overrides: dict[str, str] = {}

        def _is_news_ai_key(key: str) -> bool:
            return key.startswith("news_ai.") or key.startswith("NEWS_AI_")

        if env_token:
            suffix = f"_{env_token}"
            for cfg in configs:
                key = str(cfg.key)
                if not _is_news_ai_key(key):
                    continue
                if key.endswith(suffix):
                    base_key = key[: -len(suffix)]
                    if cfg.value is None:
                        continue
                    overrides[base_key] = str(cfg.value)

        for cfg in configs:
            key = str(cfg.key)
            if not _is_news_ai_key(key):
                continue
            if key in overrides:
                continue
            if cfg.value is None:
                continue
            overrides[key] = str(cfg.value)

        return overrides

    async def run_once(self, db: AsyncSession) -> dict[str, int]:
        """运行一次流水线处理"""
        from .summarization import news_ai_summarization_service

        overrides = await self.load_system_config_overrides(db)
        settings = get_settings()

        def _bool_value(raw: object | None, default: bool) -> bool:
            if raw is None:
                return bool(default)
            s = str(raw).strip().lower()
            if not s:
                return bool(default)
            return s in {"1", "true", "yes", "y", "on"}

        summary_enabled_raw = overrides.get("news_ai.summary_enabled")
        if summary_enabled_raw is None:
            summary_enabled_raw = os.getenv("NEWS_AI_SUMMARY_ENABLED")
        if summary_enabled_raw is None or not str(summary_enabled_raw).strip():
            summary_enabled = True
        else:
            summary_enabled = _bool_value(summary_enabled_raw, False)
        if not summary_enabled:
            logger.info("News AI summary is disabled")
            return {"pending": 0, "processed": 0,
                    "skipped": 0, "created": 0, "errors": 0}

        review_policy_enabled = _bool_value(
            os.getenv("NEWS_REVIEW_POLICY_ENABLED"), False)

        recent_threshold = datetime.now() - settings.NEWS_AI_MAX_AGE
        max_batch = int(
            overrides.get(
                "news_ai.batch_size",
                settings.NEWS_AI_BATCH_SIZE))
        max_batch = min(max_batch, 50)
        max_concurrent = int(
            overrides.get(
                "news_ai.max_concurrent",
                settings.NEWS_AI_MAX_CONCURRENT))
        max_concurrent = min(max_concurrent, 10)

        summary_condition = or_(
            News.summary.is_(None),
            and_(
                News.updated_at.is_not(None),
                News.updated_at < recent_threshold,
            ),
        )
        published_condition = or_(
            News.published_at.is_(None),
            News.published_at >= recent_threshold,
        )
        if review_policy_enabled:
            status_condition = or_(
                and_(
                    News.is_published,
                    News.review_status == "approved",
                    published_condition,
                ),
                News.review_status == "pending",
            )
        else:
            status_condition = and_(
                News.is_published,
                News.review_status == "approved",
                published_condition,
            )

        query = (
            select(News)
            .where(status_condition, summary_condition)
            .order_by(News.published_at.desc())
            .limit(max_batch)
        )

        result = await db.execute(query)
        candidates = result.scalars().all()

        pending = 0
        processed = 0
        skipped = 0
        created = 0
        errors = 0

        for news in candidates:
            try:
                news_id = int(news.id)
                existing_res = await db.execute(
                    select(NewsAIAnnotation).where(
                        NewsAIAnnotation.news_id == news_id,
                    )
                )
                existing = existing_res.scalar_one_or_none()

                if existing:
                    # Check if already processed (has processed_at)
                    if existing.processed_at is not None:
                        skipped += 1
                        continue
                else:
                    existing = NewsAIAnnotation(
                        news_id=news_id,
                        retry_count=0,
                    )
                    db.add(existing)
                    await db.flush()
                    created += 1

                pending += 1

                # Check retry count
                if existing.retry_count >= 3:
                    skipped += 1
                    continue

                annotation = await news_ai_summarization_service.process_news_ai_annotation(
                    db, news, news_id, existing
                )

                # Check if processing was successful (has processed_at)
                if annotation.processed_at is not None:
                    processed += 1
                    if review_policy_enabled and str(
                        getattr(
                            news,
                            "review_status",
                            "") or "") == "pending":
                        news.review_status = "approved"
                        if hasattr(news, "review_reason"):
                            news.review_reason = None
                        if hasattr(news, "reviewed_at"):
                            news.reviewed_at = datetime.now()
                else:
                    skipped += 1
                    errors += 1

            except IntegrityError:
                await db.rollback()
                skipped += 1
                errors += 1
            except Exception:
                logger.exception(
                    "Failed to process news %s", getattr(
                        news, "id", None))
                skipped += 1
                errors += 1

        await db.commit()
        return {
            "pending": pending,
            "processed": processed,
            "skipped": skipped,
            "created": created,
            "errors": errors,
        }

    async def rerun_news(self, db: AsyncSession, news_id: int) -> None:
        """重新处理指定的新闻"""
        from .summarization import news_ai_summarization_service

        result = await db.execute(
            select(News).where(News.id == news_id)
        )
        news = result.scalar_one_or_none()

        if not news:
            return

        # Find existing annotation for this news
        existing_res = await db.execute(
            select(NewsAIAnnotation).where(
                NewsAIAnnotation.news_id == news_id,
            )
        )
        existing = existing_res.scalar_one_or_none()

        if existing:
            # Reset for rerun (similar to original implementation)
            existing.retry_count = 0
            existing.last_error = None
            existing.last_error_at = None
            existing.summary = None
            existing.risk_level = "unknown"
            existing.keywords = None
            existing.highlights = None
        else:
            existing = NewsAIAnnotation(
                news_id=news_id,
                retry_count=0,
            )
            db.add(existing)

        await db.commit()

        await news_ai_summarization_service.process_news_ai_annotation(
            db, news, news_id, existing
        )

    async def _get_or_create_annotation(
        self, db: AsyncSession, news: News, *, news_id: int | None = None
    ) -> NewsAIAnnotation:
        """获取或创建AI标注记录"""
        n_id = news_id if news_id is not None else int(news.id)

        existing_res = await db.execute(
            select(NewsAIAnnotation).where(
                NewsAIAnnotation.news_id == n_id,
            )
        )
        existing = existing_res.scalar_one_or_none()

        if existing:
            return existing

        new_annotation = NewsAIAnnotation(
            news_id=n_id,
            status="pending",
            retry_count=0,
        )
        db.add(new_annotation)
        await db.flush()
        return new_annotation

    async def _find_duplicate_of(
            self, db: AsyncSession, news: News) -> int | None:
        """查找新闻的重复项"""
        fp = _fingerprint(news)
        title_norm = _normalize_title(news.title)
        if not title_norm:
            return None

        site = str(getattr(news, "source_site", "") or "").strip()
        candidates_q = (
            select(News.id, News.title, News.source_site)
            .where(
                and_(
                    News.id != int(news.id),
                    func.lower(News.title) == title_norm,
                    func.coalesce(News.source_site, "") == site,
                )
            )
            .order_by(News.id.asc())
            .limit(1)
        )
        res = await db.execute(candidates_q)
        row = res.first()
        if row is None:
            return None

        other_id = int(cast(int, row[0]))
        other_news_res = await db.execute(select(News).where(News.id == other_id))
        other = other_news_res.scalar_one_or_none()
        if other is None:
            return None

        if _fingerprint(other) == fp:
            return other_id
        return None

    # === 摘要生成方法（代理到 NewsAISummarizationService）===

    @staticmethod
    def _extract_structured_output(
        text: str,
        *,
        highlights_max: int,
        keywords_max: int,
        item_max_chars: int,
    ) -> tuple[str | None, list[str], list[str]]:
        """解析 LLM 输出结构"""
        from .summarization import NewsAISummarizationService

        return NewsAISummarizationService._extract_structured_output(
            text,
            highlights_max=highlights_max,
            keywords_max=keywords_max,
            item_max_chars=item_max_chars,
        )

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
        response_format: str | None = None,
        auth_header_name: str | None = None,
        auth_prefix: str | None = None,
        chat_completions_path: str | None = None,
    ) -> str:
        """代理调用 NewsAISummarizationService._llm_summarize"""
        from .summarization import news_ai_summarization_service

        if response_format is None:
            response_format = str(
                os.getenv(
                    "NEWS_AI_SUMMARY_LLM_RESPONSE_FORMAT",
                    "") or "").strip() or None

        return await news_ai_summarization_service._llm_summarize(
            api_key=api_key,
            base_url=base_url,
            model=model,
            title=title,
            content=content,
            timeout_seconds=timeout_seconds,
            summary_max_chars=summary_max_chars,
            highlights_max=highlights_max,
            keywords_max=keywords_max,
            response_format=response_format,
            auth_header_name=auth_header_name,
            auth_prefix=auth_prefix,
            chat_completions_path=chat_completions_path,
        )

    def get_summary_llm_providers(
        self,
        settings: object,
        *,
        env_overrides: dict[str, str] | None = None,
    ) -> list[_NewsSummaryLLMProvider]:
        """获取摘要 LLM providers（代理到 NewsAISummarizationService）"""
        from .summarization import news_ai_summarization_service

        return news_ai_summarization_service._get_summary_llm_providers(
            settings,
            env_overrides=env_overrides,
        )

    async def _make_summary(
        self,
        news: News,
        *,
        env_overrides: dict[str, str] | None = None,
        force_generate: bool = False,
    ) -> tuple[str | None, bool, list[str], list[str]]:
        """生成摘要（代理到 NewsAISummarizationService）"""
        from .summarization import news_ai_summarization_service
        return await news_ai_summarization_service._make_summary(
            news, env_overrides=env_overrides, force_generate=force_generate
        )

    def _make_risk(self, news: News) -> tuple[str, str | None]:
        """计算新闻风险等级（代理到 content_filter）"""
        content = str(getattr(news, "content", "") or "").strip()
        title = str(getattr(news, "title", "") or "").strip()
        text_for_filter = f"{title}\n{content}"
        filter_passed, filter_reason, _ = content_filter.check_content(
            text_for_filter)
        risk_level = _risk_from_filter(filter_passed, filter_reason)
        return risk_level, filter_reason

    def _make_summary_local(self, news: News) -> str | None:
        """本地摘要生成"""
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
        """本地高亮和关键词生成"""
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


# 单例
_news_ai_pipeline_service: NewsAIPipelineService | None = None


def get_news_ai_pipeline_service() -> NewsAIPipelineService:
    """获取新闻AI流水线服务实例"""
    global _news_ai_pipeline_service
    if _news_ai_pipeline_service is None:
        _news_ai_pipeline_service = NewsAIPipelineService()
    return _news_ai_pipeline_service


news_ai_pipeline_service = get_news_ai_pipeline_service()
