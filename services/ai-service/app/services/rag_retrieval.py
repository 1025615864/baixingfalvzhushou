"""RAG检索服务 - 三级Fallback链+缓存 (HTTP客户端模式)"""
import asyncio
import time
import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class RetrievalLevel(Enum):
    LEVEL_1_LOCAL = "level_1_local"
    LEVEL_2_BACKEND = "level_2_backend"
    LEVEL_3_FALLBACK = "level_3_fallback"


@dataclass
class RetrievedDoc:
    id: str
    content: str
    metadata: dict
    source: str
    level: str
    similarity: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
            "level": self.level,
            "similarity": self.similarity
        }


@dataclass
class RetrievalResult:
    docs: list[RetrievedDoc]
    total_count: int
    sources: dict
    latency_ms: int
    retrieval_level: str
    sufficient: bool
    cached: bool = False


class RetrievalConfig:
    """检索配置"""
    LEVEL1_TIMEOUT_MS = 10000
    LEVEL2_TIMEOUT_MS = 10000
    MIN_DOCS_THRESHOLD = 1
    HIGH_QUALITY_SIMILARITY = 0.05
    MIN_SIMILARITY_THRESHOLD = -0.2
    MAX_DOCS_PER_LEVEL = 5


class RAGRetrievalService:
    """RAG检索服务 - 三级Fallback链+缓存 (通过HTTP调用知识库/档案库服务)"""

    def __init__(self):
        self.config = RetrievalConfig()
        self._use_cache = True
        self._knowledge_client = None
        self._archive_client = None

    def _get_knowledge_client(self):
        """获取知识库HTTP客户端"""
        if self._knowledge_client is None:
            from app.services.knowledge_service_client import get_knowledge_client
            self._knowledge_client = get_knowledge_client()
        return self._knowledge_client

    def _get_archive_client(self):
        """获取档案库HTTP客户端"""
        if self._archive_client is None:
            from app.services.archive_service_client import get_archive_client
            self._archive_client = get_archive_client()
        return self._archive_client

    async def retrieve(
        self,
        query: str,
        intent: str = "legal",
        top_k: int = 5,
        conversation_id: Optional[str] = None
    ) -> RetrievalResult:
        """执行三级RAG检索（通过HTTP调用知识库/档案库服务）"""
        start_time = time.time()

        if self._use_cache:
            try:
                from app.services.retrieval_cache import get_retrieval_cache_service
                cache_service = get_retrieval_cache_service()
                cached_docs = await cache_service.get_cached_result(query, intent, top_k)

                if cached_docs:
                    cached_retrieved = [
                        RetrievedDoc(
                            id=doc.get("id", ""),
                            content=doc.get("content", doc.get("text", "")),
                            metadata=doc.get("metadata", {}),
                            source=doc.get("source", ""),
                            level=doc.get("level", "cache"),
                            similarity=doc.get("similarity", 0.9)
                        )
                        for doc in cached_docs
                    ]
                    result = RetrievalResult(
                        docs=cached_retrieved,
                        total_count=len(cached_retrieved),
                        sources={"cache_hit": len(cached_retrieved)},
                        latency_ms=0,
                        retrieval_level="cache",
                        sufficient=len(cached_retrieved) >= self.config.MIN_DOCS_THRESHOLD,
                        cached=True
                    )
                    self._log_retrieval(conversation_id, query, intent, result)
                    return result
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}")

        all_docs: list[RetrievedDoc] = []
        sources = {"level_1_local": 0, "level_2_backend": 0, "level_3_fallback": 0}
        final_level = RetrievalLevel.LEVEL_1_LOCAL

        level1_docs = await self._retrieve_level1(query, top_k)
        all_docs.extend(level1_docs)
        sources["level_1_local"] = len(level1_docs)

        level1_sufficient = self._is_sufficient(level1_docs)

        if level1_sufficient:
            final_level = RetrievalLevel.LEVEL_1_LOCAL
            final_docs = self._deduplicate_and_rerank(all_docs, top_k)

            if self._use_cache and final_docs:
                await self._cache_result(query, final_docs, "level_1_local", intent, top_k)

            latency_ms = int((time.time() - start_time) * 1000)
            result = RetrievalResult(
                docs=final_docs,
                total_count=len(final_docs),
                sources=sources,
                latency_ms=latency_ms,
                retrieval_level=final_level.value,
                sufficient=True
            )
            self._log_retrieval(conversation_id, query, intent, result)
            return result

        logger.info(f"Level 1 insufficient ({len(level1_docs)} docs), trying Level 2...")

        level2_docs = await self._retrieve_level2(query, top_k)
        all_docs.extend(level2_docs)
        sources["level_2_backend"] = len(level2_docs)

        level2_sufficient = self._is_sufficient(all_docs)

        if level2_sufficient:
            final_level = RetrievalLevel.LEVEL_2_BACKEND
            final_docs = self._deduplicate_and_rerank(all_docs, top_k)

            if self._use_cache and final_docs:
                await self._cache_result(query, final_docs, "level_2_backend", intent, top_k)

            latency_ms = int((time.time() - start_time) * 1000)
            result = RetrievalResult(
                docs=final_docs,
                total_count=len(final_docs),
                sources=sources,
                latency_ms=latency_ms,
                retrieval_level=final_level.value,
                sufficient=True
            )
            self._log_retrieval(conversation_id, query, intent, result)
            return result

        logger.warning("Level 2 insufficient, using Level 3 fallback...")

        final_level = RetrievalLevel.LEVEL_3_FALLBACK
        final_docs = self._deduplicate_and_rerank(all_docs, top_k)

        if not final_docs:
            final_docs = self._get_default_docs(query)

        sources["level_3_fallback"] = len(final_docs)
        latency_ms = int((time.time() - start_time) * 1000)
        result = RetrievalResult(
            docs=final_docs,
            total_count=len(final_docs),
            sources=sources,
            latency_ms=latency_ms,
            retrieval_level=final_level.value,
            sufficient=len(final_docs) > 0
        )
        self._log_retrieval(conversation_id, query, intent, result)
        return result

    def _log_retrieval(self, conversation_id: Optional[str], query: str, intent: str, result: RetrievalResult):
        """记录检索日志"""
        try:
            from app.database import SessionLocal
            from app.services.retrieval_log_service import RetrievalLogService

            db = SessionLocal()
            try:
                service = RetrievalLogService(db)
                service.log_retrieval(
                    conversation_id=conversation_id or "unknown",
                    query=query,
                    intent=intent,
                    retrieval_level=result.retrieval_level,
                    docs_retrieved=result.total_count,
                    docs_used=len(result.docs),
                    latency_ms=result.latency_ms,
                    cache_hit=result.cached,
                    sources=result.sources
                )
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to log retrieval: {e}")

    async def _cache_result(self, query: str, docs: list, level: str, intent: str, top_k: int):
        """缓存检索结果"""
        try:
            from app.services.retrieval_cache import get_retrieval_cache_service
            cache_service = get_retrieval_cache_service()
            await cache_service.cache_result(
                query=query,
                docs=[d.to_dict() for d in docs],
                retrieval_level=level,
                intent=intent,
                top_k=top_k
            )
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    async def _retrieve_level1(self, query: str, top_k: int) -> list[RetrievedDoc]:
        """Level 1: 通过HTTP调用知识库服务+档案库服务"""
        try:
            knowledge_client = self._get_knowledge_client()
            archive_client = self._get_archive_client()

            knowledge_results, archive_results = await asyncio.gather(
                knowledge_client.search_vector(query=query, top_k=top_k),
                archive_client.search_vector(query=query, top_k=top_k),
                return_exceptions=True
            )

            docs = []

            if isinstance(knowledge_results, list):
                for i, doc in enumerate(knowledge_results):
                    docs.append(RetrievedDoc(
                        id=doc.get("id", f"kb_{i}"),
                        content=doc.get("text", doc.get("content", "")),
                        metadata=doc.get("metadata", {}),
                        source="knowledge",
                        level="level_1_local",
                        similarity=1.0 - (doc.get("distance", 0) or 0)
                    ))

            if isinstance(archive_results, list):
                for i, doc in enumerate(archive_results):
                    docs.append(RetrievedDoc(
                        id=doc.get("id", f"arc_{i}"),
                        content=doc.get("text", doc.get("content", "")),
                        metadata=doc.get("metadata", {}),
                        source="archive",
                        level="level_1_local",
                        similarity=1.0 - (doc.get("distance", 0) or 0)
                    ))

            docs = [d for d in docs if d.similarity >= self.config.MIN_SIMILARITY_THRESHOLD]
            return docs
        except Exception as e:
            logger.error(f"Level 1 error: {e}")
            return []

    async def _retrieve_level2(self, query: str, top_k: int) -> list[RetrievedDoc]:
        """Level 2: Backend远程RAG"""
        try:
            docs = await asyncio.wait_for(
                self._search_backend_rag(query, top_k),
                timeout=self.config.LEVEL2_TIMEOUT_MS / 1000
            )
            logger.info(f"Level 2 retrieved {len(docs)} docs")
            return docs
        except asyncio.TimeoutError:
            logger.warning("Level 2 timeout")
            return []
        except Exception as e:
            logger.error(f"Level 2 error: {e}")
            return []

    async def _search_backend_rag(self, query: str, top_k: int) -> list[RetrievedDoc]:
        """搜索Backend RAG"""
        try:
            from app.services.backend_rag_client import query_backend_knowledge
            result = await query_backend_knowledge(question=query, top_k=top_k)

            if not result or result.get("retrieved_documents", 0) == 0:
                return []

            sources = result.get("sources", [])
            return [
                RetrievedDoc(
                    id=f"backend_{i}",
                    content=src.get("content", ""),
                    metadata={"source": "backend", "url": src.get("url", "")},
                    source="backend",
                    level="level_2_backend",
                    similarity=src.get("score", 0.8)
                )
                for i, src in enumerate(sources)
            ]
        except Exception as e:
            logger.error(f"Backend RAG search error: {e}")
            return []

    def _is_sufficient(self, docs: list[RetrievedDoc]) -> bool:
        """判断检索结果是否充分"""
        if len(docs) < self.config.MIN_DOCS_THRESHOLD:
            return False

        if docs:
            max_similarity = max(d.similarity for d in docs)
            return max_similarity >= self.config.HIGH_QUALITY_SIMILARITY

        return False

    def _deduplicate_and_rerank(
        self,
        docs: list[RetrievedDoc],
        top_k: int
    ) -> list[RetrievedDoc]:
        """去重+重排序"""
        seen_contents = set()
        unique_docs = []

        for doc in sorted(docs, key=lambda d: d.similarity, reverse=True):
            content_key = doc.content[:100]
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                unique_docs.append(doc)

        return unique_docs[:top_k]

    def _get_default_docs(self, query: str) -> list[RetrievedDoc]:
        """获取默认文档（无检索结果时）"""
        return [
            RetrievedDoc(
                id="default_1",
                content="根据《中华人民共和国民法典》第一千一百六十五条，行为人因过错侵害他人民事权益造成损害的，应当承担侵权责任。",
                metadata={
                    "law_name": "民法典",
                    "article_num": "第1165条",
                    "category": "侵权责任"
                },
                source="default",
                level="level_3_fallback",
                similarity=0.5
            ),
            RetrievedDoc(
                id="default_2",
                content="根据《中华人民共和国劳动法》第四十四条，用人单位应当按时足额支付劳动者工资，不得克扣或者无故拖欠。",
                metadata={
                    "law_name": "劳动法",
                    "article_num": "第44条",
                    "category": "劳动报酬"
                },
                source="default",
                level="level_3_fallback",
                similarity=0.5
            )
        ]


rag_retrieval_service = RAGRetrievalService()


async def retrieve_with_fallback(
    query: str,
    intent: str = "legal",
    top_k: int = 5
) -> RetrievalResult:
    """便捷函数：带Fallback的RAG检索"""
    return await rag_retrieval_service.retrieve(query, intent, top_k)
