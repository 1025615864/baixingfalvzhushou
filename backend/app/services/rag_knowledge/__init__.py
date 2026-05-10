"""RAG knowledge service."""
from __future__ import annotations
import time
import uuid
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class KnowledgeDocument:
    id: str
    title: str
    content: str
    source: Optional[str] = None
    category: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    embedding: Optional[list[float]] = None


@dataclass
class SearchResult:
    document: KnowledgeDocument
    score: float
    snippet: str = ""


class KnowledgeBaseManager:
    def __init__(self):
        self._documents: dict[str, dict] = {}
        self._chunks: list[dict] = []
        self._data_sources: dict[str, dict] = {}
        self._next_doc_id = 1
        self._next_source_id = 1

    def _chunk_content(self, content: str, doc_id: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
        chunks = []
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunk_text = content[start:end]
            chunks.append({
                "id": len(self._chunks) + len(chunks) + 1,
                "document_id": doc_id,
                "content": chunk_text,
            })
            start += chunk_size - overlap
            if start >= len(content):
                break
        return chunks

    async def add_document(self, title: str, content: str, source_type: str = "manual") -> dict:
        doc_id = f"doc_{self._next_doc_id}"
        self._next_doc_id += 1
        chunks = self._chunk_content(content, doc_id)
        doc = {
            "id": doc_id,
            "title": title,
            "content": content,
            "source_type": source_type,
            "chunk_count": len(chunks),
        }
        self._documents[doc_id] = doc
        self._chunks.extend(chunks)
        return doc

    async def get_documents(self) -> list[dict]:
        return list(self._documents.values())

    async def add_data_source(self, name: str, source_type: str, config: dict) -> dict:
        source_id = f"src_{self._next_source_id}"
        self._next_source_id += 1
        source = {
            "source_id": source_id,
            "name": name,
            "type": source_type,
            "config": config,
            "status": "active",
        }
        self._data_sources[source_id] = source
        return source

    async def sync_data_source(self, source_id: str) -> dict:
        source = self._data_sources.get(source_id)
        if not source:
            return {"success": False, "error": "数据源不存在"}
        source["synced_at"] = time.time()
        return {"success": True, "synced_at": source["synced_at"]}


class RetrievalOptimizer:
    STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "and", "or"}

    def __init__(self):
        self._index: dict[str, list[dict]] = {}

    def _extract_keywords(self, content: str) -> set[str]:
        words = content.lower().split()
        return {w for w in words if w not in self.STOP_WORDS and len(w) > 1}

    def build_index(self, chunks: list[dict]) -> None:
        self._index.clear()
        for chunk in chunks:
            keywords = self._extract_keywords(chunk.get("content", ""))
            for keyword in keywords:
                if keyword not in self._index:
                    self._index[keyword] = []
                self._index[keyword].append(chunk)

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        query_keywords = self._extract_keywords(query)
        matched_chunks: dict[int, tuple[dict, int]] = {}
        for keyword in query_keywords:
            for chunk in self._index.get(keyword, []):
                chunk_id = chunk.get("id", id(chunk))
                if chunk_id not in matched_chunks:
                    matched_chunks[chunk_id] = (chunk, 0)
                chunk_data, count = matched_chunks[chunk_id]
                matched_chunks[chunk_id] = (chunk_data, count + 1)
        sorted_results = sorted(matched_chunks.values(), key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in sorted_results[:top_k]]

    async def rerank(self, query: str, candidates: list[dict]) -> list[dict]:
        query_keywords = self._extract_keywords(query)
        scored = []
        for candidate in candidates:
            content_keywords = self._extract_keywords(candidate.get("content", ""))
            overlap = len(query_keywords & content_keywords)
            scored.append((candidate, overlap))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored]


class RAGService:
    def __init__(self):
        self.knowledge_base = KnowledgeBaseManager()
        self.retrieval_optimizer = RetrievalOptimizer()

    async def enhance_knowledge_base(self, sources: list[dict]) -> dict:
        documents_added = 0
        for source_config in sources:
            source = await self.knowledge_base.add_data_source(
                name=source_config.get("name", ""),
                source_type=source_config.get("type", "manual"),
                config=source_config.get("config", {}),
            )
            documents_added += 1
        docs = await self.knowledge_base.get_documents()
        chunks = []
        for doc in docs:
            doc_chunks = [c for c in [] if c.get("document_id") == doc["id"]]
            chunks.extend(doc_chunks)
        self.retrieval_optimizer.build_index(chunks)
        return {"documents_added": documents_added, "chunks_indexed": len(chunks)}

    async def query(self, query: str, top_k: int = 5) -> dict:
        results = await self.retrieval_optimizer.search(query, top_k)
        context = "\n".join(r.get("content", "") for r in results)
        return {
            "retrieved_documents": len(results),
            "context": context,
            "results": results,
        }


class RAGKnowledgeService:
    def __init__(self):
        self._documents: dict[str, KnowledgeDocument] = {}
        self._next_id = 1

    async def add_document(self, title: str, content: str, source: Optional[str] = None, category: Optional[str] = None) -> KnowledgeDocument:
        doc_id = f"doc_{self._next_id}"
        self._next_id += 1
        doc = KnowledgeDocument(id=doc_id, title=title, content=content, source=source, category=category)
        self._documents[doc_id] = doc
        return doc

    async def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        return self._documents.get(doc_id)

    async def search(self, query: str, k: int = 5, category: Optional[str] = None) -> list[SearchResult]:
        results = []
        for doc in self._documents.values():
            if category and doc.category != category:
                continue
            if query.lower() in doc.content.lower() or query.lower() in doc.title.lower():
                score = 1.0 if query.lower() in doc.title.lower() else 0.5
                snippet = doc.content[:200]
                results.append(SearchResult(document=doc, score=score, snippet=snippet))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]

    async def delete_document(self, doc_id: str) -> dict:
        if doc_id not in self._documents:
            return {"success": False, "error": "文档不存在"}
        del self._documents[doc_id]
        return {"success": True}

    async def list_documents(self, category: Optional[str] = None, limit: int = 20) -> list[KnowledgeDocument]:
        docs = list(self._documents.values())
        if category:
            docs = [d for d in docs if d.category == category]
        return docs[:limit]


rag_knowledge_service = RAGKnowledgeService()
