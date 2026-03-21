"""RAG 知识库服务

提供知识库增强、数据源扩充、检索优化等功能。
集成缓存优化：向量检索缓存、结果去重、批量检索优化。
"""
import logging
from datetime import datetime, timezone
from typing import Any

from .ai.cache_optimizer import (
    get_ai_cache_optimizer,
    VectorSearchCache,
    ResultDeduplicator,
    BatchRetrievalOptimizer,
    CachePriority,
)

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """知识库管理器"""

    def __init__(self):
        self._documents: dict[int, dict[str, Any]] = {}
        self._chunks: list[dict[str, Any]] = []
        self._data_sources: dict[str, dict[str, Any]] = {}

    async def add_document(
        self,
        title: str,
        content: str,
        source_type: str = "manual",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """添加文档

        Args:
            title: 标题
            content: 内容
            source_type: 来源类型
            metadata: 元数据

        Returns:
            文档信息
        """
        doc_id = len(self._documents) + 1
        now = datetime.now(timezone.utc).isoformat()

        document = {
            "id": doc_id,
            "title": title,
            "content": content,
            "source_type": source_type,
            "metadata": metadata or {},
            "status": "indexed",
            "created_at": now,
            "updated_at": now,
            "chunk_count": 0,
        }

        self._documents[doc_id] = document

        chunks = self._chunk_content(content, doc_id)
        self._chunks.extend(chunks)
        document["chunk_count"] = len(chunks)

        logger.info(f"Added document {doc_id}: {title}")

        return {
            "document_id": doc_id,
            "title": title,
            "chunk_count": len(chunks),
            "created_at": now,
        }

    def _chunk_content(
        self,
        content: str,
        doc_id: int,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> list[dict[str, Any]]:
        """切分内容

        Args:
            content: 内容
            doc_id: 文档ID
            chunk_size: 块大小
            overlap: 重叠大小

        Returns:
            块列表
        """
        chunks = []
        chars = list(content)
        num_chunks = (len(chars) + chunk_size - overlap -
                      1) // (chunk_size - overlap) + 1

        for i in range(num_chunks):
            start = i * (chunk_size - overlap)
            end = min(start + chunk_size, len(chars))
            chunk_content = "".join(chars[start:end])

            if chunk_content.strip():
                chunks.append({
                    "id": len(self._chunks) + i + 1,
                    "document_id": doc_id,
                    "content": chunk_content,
                    "start_char": start,
                    "end_char": end,
                })

        return chunks

    async def add_data_source(
        self,
        name: str,
        source_type: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """添加数据源

        Args:
            name: 名称
            source_type: 来源类型
            config: 配置

        Returns:
            数据源信息
        """
        source_id = f"DS-{len(self._data_sources) + 1:04d}"
        now = datetime.now(timezone.utc).isoformat()

        source = {
            "id": source_id,
            "name": name,
            "source_type": source_type,
            "config": config,
            "status": "active",
            "last_sync": now,
            "document_count": 0,
        }

        self._data_sources[source_id] = source

        logger.info(f"Added data source {source_id}: {name}")

        return {
            "source_id": source_id,
            "name": name,
            "status": "active",
        }

    async def sync_data_source(self, source_id: str) -> dict[str, Any]:
        """同步数据源

        Args:
            source_id: 数据源ID

        Returns:
            同步结果
        """
        source = self._data_sources.get(source_id)

        if not source:
            return {
                "success": False,
                "error": "数据源不存在",
            }

        source["last_sync"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Synced data source {source_id}")

        return {
            "success": True,
            "source_id": source_id,
            "synced_at": source["last_sync"],
        }

    async def get_documents(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """获取文档列表

        Args:
            status: 状态筛选
            limit: 限制数量

        Returns:
            文档列表
        """
        docs = list(self._documents.values())

        if status:
            docs = [d for d in docs if d["status"] == status]

        return docs[:limit]


class RetrievalOptimizer:
    """检索优化器
    
    集成了缓存和去重功能的检索优化器。
    """

    def __init__(self, use_cache: bool = True):
        self._index: dict[str, list[dict[str, Any]]] = {}
        self._weights: dict[str, float] = {}
        
        # 缓存相关组件
        self._use_cache = use_cache
        self._cache: VectorSearchCache | None = None
        self._deduplicator: ResultDeduplicator | None = None
        self._batch_optimizer: BatchRetrievalOptimizer | None = None
        
        if use_cache:
            try:
                cache_optimizer = get_ai_cache_optimizer()
                self._cache = cache_optimizer.vector_search_cache
                self._deduplicator = cache_optimizer.deduplicator
                self._batch_optimizer = cache_optimizer.batch_optimizer
                logger.info("RetrievalOptimizer cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize cache: {e}")

    def build_index(self, chunks: list[dict[str, Any]]) -> None:
        """构建索引

        Args:
            chunks: 块列表
        """
        for chunk in chunks:
            keywords = self._extract_keywords(chunk["content"])

            for keyword in keywords:
                if keyword not in self._index:
                    self._index[keyword] = []
                self._index[keyword].append(chunk)

        logger.info(f"Built index with {len(self._index)} keywords")

    def _extract_keywords(self, content: str) -> list[str]:
        """提取关键词

        Args:
            content: 内容

        Returns:
            关键词列表
        """
        words = content.lower().split()
        stop_words = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "自己",
            "这"}

        keywords = [w for w in words if w not in stop_words and len(w) > 1]

        return list(set(keywords))

    def set_field_weight(self, field: str, weight: float) -> None:
        """设置字段权重

        Args:
            field: 字段
            weight: 权重
        """
        self._weights[field] = weight

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        use_cache: bool | None = None,
        deduplicate: bool = True,
    ) -> list[dict[str, Any]]:
        """搜索

        Args:
            query: 查询词
            top_k: 返回数量
            filters: 筛选条件
            use_cache: 是否使用缓存
            deduplicate: 是否对结果去重

        Returns:
            结果列表
        """
        effective_use_cache = use_cache if use_cache is not None else self._use_cache
        
        # 尝试从缓存获取
        if effective_use_cache and self._cache is not None:
            try:
                cached_results = self._cache.get_sync(query, top_k)
                if cached_results is not None:
                    logger.debug(f"RetrievalOptimizer cache hit for query: {query[:50]}...")
                    # 转换缓存格式
                    return [{"id": r[1].get("id"), "content": r[0], "metadata": r[1], "score": r[2]}
                            for r in cached_results]
            except Exception as e:
                logger.debug(f"Cache get error: {e}")
        
        keywords = self._extract_keywords(query)
        results: dict[int, dict[str, Any]] = {}

        for keyword in keywords:
            if keyword in self._index:
                for chunk in self._index[keyword]:
                    chunk_id = chunk["id"]
                    if chunk_id not in results:
                        results[chunk_id] = {
                            "chunk": chunk,
                            "score": 0,
                            "matched_keywords": [],
                        }
                    results[chunk_id]["score"] += 1
                    results[chunk_id]["matched_keywords"].append(keyword)

        sorted_results = sorted(
            results.values(),
            key=lambda x: x["score"],
            reverse=True)
        
        result_chunks = [r["chunk"] for r in sorted_results[:top_k]]
        
        # 去重处理
        if deduplicate and self._deduplicator is not None and result_chunks:
            # 转换为去重器期望的格式
            dedupe_input = [
                (c.get("content", ""), c, c.get("score", 0))
                for c in result_chunks
            ]
            deduped = self._deduplicator.deduplicate(dedupe_input)
            result_chunks = [r[1] for r in deduped]
            logger.debug(f"Deduplicated results: {len(result_chunks)} items")
        
        # 存入缓存
        if effective_use_cache and self._cache is not None and result_chunks:
            try:
                cache_entries = [
                    (c.get("content", ""), c, c.get("score", 0))
                    for c in result_chunks
                ]
                self._cache.set_sync(query, cache_entries, top_k, ttl=600)
                logger.debug(f"Cached results for query: {query[:50]}...")
            except Exception as e:
                logger.debug(f"Cache set error: {e}")

        return result_chunks

    async def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """重排序

        Args:
            query: 查询词
            candidates: 候选列表

        Returns:
            重排序后的列表
        """
        query_keywords = set(self._extract_keywords(query))

        for candidate in candidates:
            content_keywords = set(
                self._extract_keywords(
                    candidate.get(
                        "content", "")))
            overlap = len(query_keywords & content_keywords)
            candidate["relevance_score"] = overlap / \
                max(len(query_keywords), 1)

        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True,
        )

        return sorted_candidates


class RAGService:
    """RAG 服务
    
    集成了缓存优化的 RAG 服务。
    """

    def __init__(self, use_cache: bool = True):
        self.knowledge_base = KnowledgeBaseManager()
        self.retrieval_optimizer = RetrievalOptimizer(use_cache=use_cache)
        self._use_cache = use_cache

    async def enhance_knowledge_base(
        self,
        data_sources: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """增强知识库

        Args:
            data_sources: 数据源列表

        Returns:
            增强结果
        """
        total_docs = 0
        total_chunks = 0

        for source in data_sources:
            result = await self.knowledge_base.add_data_source(
                name=source["name"],
                source_type=source["type"],
                config=source.get("config", {}),
            )
            total_docs += 1

        docs = await self.knowledge_base.get_documents()
        chunks = []
        for doc in docs:
            doc_chunks = [c for c in [] if c["document_id"] == doc["id"]]
            chunks.extend(doc_chunks)
            total_chunks += len(doc_chunks)

        self.retrieval_optimizer.build_index(chunks)

        return {
            "documents_added": total_docs,
            "chunks_indexed": total_chunks,
            "keywords_indexed": len(self.retrieval_optimizer._index),
            "enhanced_at": datetime.now(timezone.utc).isoformat(),
        }

    async def query(
        self,
        question: str,
        top_k: int = 5,
        use_rerank: bool = True,
        use_cache: bool | None = None,
        deduplicate: bool = True,
    ) -> dict[str, Any]:
        """查询

        Args:
            question: 问题
            top_k: 返回数量
            use_rerank: 是否重排序
            use_cache: 是否使用缓存
            deduplicate: 是否对结果去重

        Returns:
            查询结果
        """
        effective_use_cache = use_cache if use_cache is not None else self._use_cache
        
        candidates = await self.retrieval_optimizer.search(
            query=question,
            top_k=top_k * 2,
            use_cache=effective_use_cache,
            deduplicate=deduplicate,
        )

        if use_rerank and candidates:
            candidates = await self.retrieval_optimizer.rerank(query=question, candidates=candidates)
            candidates = candidates[:top_k]

        context = "\n".join([c.get("content", "") for c in candidates])

        return {
            "question": question,
            "context": context,
            "retrieved_documents": len(candidates),
            "sources": [
                {"id": c.get("document_id"), "title": ""}
                for c in candidates
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    
    async def batch_query(
        self,
        questions: list[str],
        top_k: int = 5,
        use_rerank: bool = True,
        use_cache: bool | None = None,
        deduplicate: bool = True,
    ) -> list[dict[str, Any]]:
        """批量查询

        利用缓存优化批量检索性能。

        Args:
            questions: 问题列表
            top_k: 每个问题返回数量
            use_rerank: 是否重排序
            use_cache: 是否使用缓存
            deduplicate: 是否对结果去重

        Returns:
            查询结果列表
        """
        results = []
        for question in questions:
            result = await self.query(
                question=question,
                top_k=top_k,
                use_rerank=use_rerank,
                use_cache=use_cache,
                deduplicate=deduplicate,
            )
            results.append(result)
        return results
    
    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息

        Returns:
            缓存统计信息
        """
        if self.retrieval_optimizer._cache is None:
            return {"cache_enabled": False}
        
        return {
            "cache_enabled": True,
            "cache_stats": self.retrieval_optimizer._cache.get_stats(),
        }
    
    async def invalidate_cache(self, query: str | None = None) -> int:
        """使缓存失效

        Args:
            query: 特定查询文本，如果为 None 则清除所有缓存

        Returns:
            失效的缓存条目数
        """
        if self.retrieval_optimizer._cache is None:
            return 0
        
        try:
            if query is not None:
                await self.retrieval_optimizer._cache.invalidate(query)
                return 1
            else:
                return await self.retrieval_optimizer._cache.invalidate_all()
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return 0

    async def get_retrieval_metrics(self) -> dict[str, Any]:
        """获取检索指标

        Returns:
            指标数据
        """
        return {
            "indexed_keywords": len(
                self.retrieval_optimizer._index),
            "indexed_chunks": sum(
                len(v) for v in self.retrieval_optimizer._index.values()),
            "field_weights": self.retrieval_optimizer._weights,
        }


# 单例实例
rag_service = RAGService()


async def enhance_knowledge_base(
    data_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    """便捷函数：增强知识库

    Args:
        data_sources: 数据源列表

    Returns:
        增强结果
    """
    return await rag_service.enhance_knowledge_base(data_sources=data_sources)


async def query_knowledge_base(
    question: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """便捷函数：查询知识库

    Args:
        question: 问题
        top_k: 返回数量

    Returns:
        查询结果
    """
    return await rag_service.query(question=question, top_k=top_k)


async def get_retrieval_metrics() -> dict[str, Any]:
    """便捷函数：获取检索指标

    Returns:
        指标数据
    """
    return await rag_service.get_retrieval_metrics()
