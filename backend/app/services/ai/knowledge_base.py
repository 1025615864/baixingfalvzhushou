"""AI knowledge base service."""
from __future__ import annotations
from typing import Optional
from dataclasses import dataclass


@dataclass
class QualityResult:
    total_candidates: int = 0
    qualified_count: int = 0
    avg_similarity: float = 0.0
    confidence: str = "low"


class LegalKnowledgeBase:
    RELEVANCE_THRESHOLD: float = 0.5
    MIN_REFERENCES: int = 1
    MAX_REFERENCES: int = 5

    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return
        try:
            from app.core.config import settings
            if settings.openai_api_key:
                try:
                    from langchain_openai import OpenAIEmbeddings
                    from langchain_community.vectorstores import Chroma
                    self.embeddings = OpenAIEmbeddings(
                        openai_api_key=settings.openai_api_key,
                        openai_api_base=getattr(settings, 'openai_base_url', None),
                    )
                    self.vector_store = Chroma(
                        persist_directory=getattr(settings, 'chroma_persist_dir', './chroma_db'),
                        embedding_function=self.embeddings,
                    )
                except Exception:
                    self.embeddings = None
                    self.vector_store = None
        except Exception:
            pass
        self._initialized = True

    def search(self, query: str, k: int = 5) -> list[tuple[str, dict, float]]:
        if not self._initialized:
            self.initialize()
        if self.vector_store is None:
            return []
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return [(doc.page_content, doc.metadata, self._score_to_similarity(score)) for doc, score in results]
        except Exception:
            return []

    def search_with_quality_control(self, query: str, k: int = 5, threshold: float = 0.5) -> tuple[list[tuple[str, dict, float]], QualityResult]:
        results = self.search(query, k=k)
        qualified = [r for r in results if r[2] >= threshold]
        qualified = qualified[:self.MAX_REFERENCES]
        avg_sim = sum(r[2] for r in qualified) / len(qualified) if qualified else 0.0
        confidence = self._calculate_confidence(qualified)
        quality = QualityResult(
            total_candidates=len(results),
            qualified_count=len(qualified),
            avg_similarity=avg_sim,
            confidence=confidence,
        )
        return qualified, quality

    def add_law_documents(self, documents: list[dict]) -> None:
        if not self._initialized:
            self.initialize()
        if not documents or self.vector_store is None:
            return
        texts = []
        metadatas = []
        for doc in documents:
            law_name = doc.get("law_name", "") or ""
            article = doc.get("article", "") or ""
            content = doc.get("content", "") or ""
            text = f"【{law_name}】{article}\n{content}"
            metadata = {
                "law_name": str(law_name),
                "article": str(article),
                "source": str(doc.get("source", "")),
                "source_url": str(doc.get("source_url", "")),
                "source_version": str(doc.get("source_version", "")),
                "source_hash": str(doc.get("source_hash", "")),
                "ingest_batch_id": str(doc.get("ingest_batch_id", "")),
                "knowledge_id": str(doc.get("knowledge_id", "")),
            }
            texts.append(text)
            metadatas.append(metadata)
        self.vector_store.add_texts(texts=texts, metadatas=metadatas)

    def _score_to_similarity(self, score: float) -> float:
        if score <= 0:
            return 1.0
        if score <= 1.0:
            return 1.0 - score
        return 1.0 / (1.0 + score)

    def _calculate_confidence(self, results: list[tuple]) -> str:
        if not results:
            return "low"
        avg = sum(r[2] for r in results) / len(results)
        if avg >= 0.85 and len(results) >= 2:
            return "high"
        if avg >= 0.7:
            return "medium"
        return "low"
