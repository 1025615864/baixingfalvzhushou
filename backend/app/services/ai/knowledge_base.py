"""法律知识库管理

支持向量检索缓存、结果去重、批量检索优化。
"""
from __future__ import annotations

import logging
from typing import cast, Any

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import SecretStr

from ...config import get_settings
from ..ai_response_strategy import SearchQuality
from .cache_optimizer import (
    get_ai_cache_optimizer,
    VectorSearchCache,
    ResultDeduplicator,
    CachePriority,
)

settings = get_settings()
logger = logging.getLogger(__name__)


class LegalKnowledgeBase:

    """法律知识库管理

    集成了缓存优化功能，包括：
    - 向量检索缓存
    - 结果去重
    - 批量检索优化
    """

    RELEVANCE_THRESHOLD: float = 0.5

    MIN_REFERENCES: int = 1

    MAX_REFERENCES: int = 5

    # 缓存配置
    CACHE_TTL: int = 600  # 10 分钟
    DEDUPE_SIMILARITY_THRESHOLD: float = 0.9

    def __init__(self, use_cache: bool = True):

        self.embeddings: OpenAIEmbeddings | None = None

        self.vector_store: Chroma | None = None

        self.text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", "。", "；", " "])

        self._initialized: bool = False
        
        # 缓存相关组件
        self._use_cache = use_cache
        self._cache: VectorSearchCache | None = None
        self._deduplicator: ResultDeduplicator | None = None
        
        if use_cache:
            try:
                cache_optimizer = get_ai_cache_optimizer()
                self._cache = cache_optimizer.vector_search_cache
                self._deduplicator = cache_optimizer.deduplicator
                logger.info("Knowledge base cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize cache: {e}")
                self._cache = None
                self._deduplicator = None

    def initialize(self):
        """初始化或加载向量数据库"""

        if self._initialized:

            return

        try:

            if settings.openai_api_key:

                self.embeddings = OpenAIEmbeddings(

                    api_key=SecretStr(settings.openai_api_key),

                    base_url=settings.openai_base_url

                )

                self.vector_store = Chroma(

                    persist_directory=settings.chroma_persist_dir,

                    embedding_function=self.embeddings,

                    collection_name="legal_knowledge"

                )

            self._initialized = True

        except Exception:

            logger.exception("初始化向量数据库失败")

            # 初始化失败时不标记为已初始化，允许后续重试
            self._initialized = False
            self.vector_store = None

    def add_law_documents(self, documents: list[dict[str, object]]):
        """添加法律文档到知识库

        Args:
            documents: 法律文档列表，每个文档包含 law_name, article, content
        """

        if not self.vector_store:

            self.initialize()

        texts: list[str] = []

        metadatas: list[dict[str, str]] = []

        for doc in documents:

            content = f"【{str(doc.get('law_name', ''))}】{str(doc.get('article', ''))}\n{str(doc.get('content', ''))}"

            texts.append(content)

            metadatas.append(

                {

                    "law_name": str(doc.get("law_name", "")),

                    "article": str(doc.get("article", "")),

                    "source": str(doc.get("source", "")),

                    "source_url": str(doc.get("source_url", "")),

                    "source_version": str(doc.get("source_version", "")),

                    "source_hash": str(doc.get("source_hash", "")),

                    "ingest_batch_id": str(doc.get("ingest_batch_id", "")),

                    "knowledge_id": str(doc.get("knowledge_id", "")),

                }

            )

        if texts and self.vector_store:

            add_texts = getattr(self.vector_store, "add_texts", None)

            if callable(add_texts):

                _ = add_texts(texts=texts, metadatas=metadatas)

    def search(
        self,
        query: str,
        k: int = 5,
        use_cache: bool | None = None,
        deduplicate: bool = True,
    ) -> list[tuple[str, dict[str, object], float]]:
        """搜索相关法律条文

        Args:
            query: 查询文本
            k: 返回结果数量
            use_cache: 是否使用缓存（None 表示使用实例默认设置）
            deduplicate: 是否对结果去重

        Returns:
            List of (content, metadata, score)
        """
        effective_use_cache = use_cache if use_cache is not None else self._use_cache

        # 尝试从缓存获取
        if effective_use_cache and self._cache is not None:
            try:
                cached_results = self._cache.get_sync(query, k)
                if cached_results is not None:
                    logger.debug(f"Cache hit for query: {query[:50]}...")
                    return cached_results
            except Exception as e:
                logger.debug(f"Cache get error: {e}")

        if not self.vector_store:
            self.initialize()

        if self.vector_store is None:
            return []

        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)

            packed: list[tuple[str, dict[str, object], float]] = []

            for doc, score in results:
                doc_obj = cast(object, doc)
                content = str(getattr(doc_obj, "page_content", ""))
                metadata_raw = getattr(doc_obj, "metadata", {})

                if not isinstance(metadata_raw, dict):
                    metadata_raw = {}

                similarity = self._score_to_similarity(float(score))

                packed.append(
                    (content, cast(dict[str, object], metadata_raw), similarity)
                )

            # 去重处理
            if deduplicate and self._deduplicator is not None:
                packed = self._deduplicator.deduplicate(packed)
                logger.debug(f"Deduplicated results: {len(packed)} items")

            # 存入缓存
            if effective_use_cache and self._cache is not None and packed:
                try:
                    self._cache.set_sync(query, packed, k, ttl=self.CACHE_TTL)
                    logger.debug(f"Cached results for query: {query[:50]}...")
                except Exception as e:
                    logger.debug(f"Cache set error: {e}")

            return packed

        except Exception:
            logger.exception("搜索失败")
            return []

    def search_with_quality_control(

        self,

        query: str,

        *,

        k: int = 5,

        threshold: float | None = None,
        
        use_cache: bool | None = None,
        
        deduplicate: bool = True,

    ) -> tuple[list[tuple[str, dict[str, object], float]], SearchQuality]:
        """带质量控制搜索相关法律条文

        Args:
            query: 查询文本
            k: 返回结果数量
            threshold: 相关性阈值
            use_cache: 是否使用缓存
            deduplicate: 是否对结果去重

        Returns:
            Tuple of (filtered results, search quality)
        """

        th = float(
            self.RELEVANCE_THRESHOLD if threshold is None else threshold)

        candidates = self.search(query, k=k, use_cache=use_cache, deduplicate=deduplicate)

        filtered = [r for r in candidates if float(r[2]) >= th]

        filtered = filtered[: int(self.MAX_REFERENCES)]

        if filtered:

            avg_similarity = sum(float(r[2])
                                 for r in filtered) / float(len(filtered))

        else:

            avg_similarity = 0.0

        confidence = self._calculate_confidence(filtered)

        return (

            filtered,

            SearchQuality(

                total_candidates=len(candidates),

                qualified_count=len(filtered),

                avg_similarity=float(avg_similarity),

                confidence=str(confidence),

            ),

        )
    
    async def batch_search(
        self,
        queries: list[str],
        k: int = 5,
        use_cache: bool | None = None,
        deduplicate: bool = True,
    ) -> dict[str, list[tuple[str, dict[str, object], float]]]:
        """批量搜索多个查询

        利用缓存优化批量检索性能。

        Args:
            queries: 查询文本列表
            k: 每个查询返回的结果数量
            use_cache: 是否使用缓存
            deduplicate: 是否对结果去重

        Returns:
            Dict mapping query to results
        """
        results = {}
        for query in queries:
            results[query] = self.search(
                query, k=k, use_cache=use_cache, deduplicate=deduplicate
            )
        return results
    
    def invalidate_cache(self, query: str | None = None) -> int:
        """使缓存失效

        Args:
            query: 特定查询文本，如果为 None 则清除所有缓存

        Returns:
            失效的缓存条目数
        """
        if self._cache is None:
            return 0
        
        try:
            if query is not None:
                # 使特定查询的缓存失效
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._cache.invalidate(query))
                return 1
            else:
                # 清除所有缓存
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._cache.invalidate_all())
                return 0  # 异步操作，无法获取确切数量
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return 0
    
    def get_cache_stats(self) -> dict[str, Any] | None:
        """获取缓存统计信息

        Returns:
            缓存统计信息字典，如果缓存未启用则返回 None
        """
        if self._cache is None:
            return None
        return self._cache.get_stats()

    def _calculate_confidence(
            self, results: list[tuple[str, dict[str, object], float]]) -> str:

        if not results:

            return "low"

        avg = sum(float(r[2]) for r in results) / float(len(results))

        if avg >= 0.85 and len(results) >= 2:

            return "high"

        if avg >= 0.7:

            return "medium"

        return "low"

    def _score_to_similarity(self, score: float) -> float:

        if score <= 0:

            return 1.0

        if score <= 1:

            sim = 1.0 - score

        else:

            sim = 1.0 / (1.0 + score)

        if sim < 0:

            return 0.0

        if sim > 1:

            return 1.0

        return float(sim)