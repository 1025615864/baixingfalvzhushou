"""法律知识库管理"""
from __future__ import annotations

import logging
from typing import cast

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import SecretStr

from ...config import get_settings
from ..ai_response_strategy import SearchQuality

settings = get_settings()
logger = logging.getLogger(__name__)


class LegalKnowledgeBase:

    """法律知识库管理"""

    RELEVANCE_THRESHOLD: float = 0.5

    MIN_REFERENCES: int = 1

    MAX_REFERENCES: int = 5

    def __init__(self):

        self.embeddings: OpenAIEmbeddings | None = None

        self.vector_store: Chroma | None = None

        self.text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", "。", "；", " "])

        self._initialized: bool = False

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

            self._initialized = True

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

    def search(self, query: str,
               k: int = 5) -> list[tuple[str, dict[str, object], float]]:
        """搜索相关法律条文



        Args:

            query: 查询文本

            k: 返回结果数量



        Returns:

            List of (content, metadata, score)

        """

        if not self.vector_store:

            self.initialize()

        if self.vector_store is None:

            return []

        try:

            results = self.vector_store.similarity_search_with_score(
                query, k=k)

            packed: list[tuple[str, dict[str, object], float]] = []

            for doc, score in results:

                doc_obj = cast(object, doc)

                content = str(getattr(doc_obj, "page_content", ""))

                metadata_raw = getattr(doc_obj, "metadata", {})

                if not isinstance(metadata_raw, dict):

                    metadata_raw = {}

                similarity = self._score_to_similarity(float(score))

                packed.append(
                    (content, cast(dict[str, object], metadata_raw), similarity))

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

    ) -> tuple[list[tuple[str, dict[str, object], float]], SearchQuality]:

        th = float(
            self.RELEVANCE_THRESHOLD if threshold is None else threshold)

        candidates = self.search(query, k=k)

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
