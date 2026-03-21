"""
RAG 检索服务 - 基于 Chroma 向量数据库

实现法律文档的向量化存储和混合检索
"""

from typing import List, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from ..config.settings import get_settings

settings = get_settings()


class LegalRetrieverService:
    """
    法律文档检索服务

    支持：
    - 混合检索 (Dense Vector + BM25 Keyword)
    - 元数据过滤
    - 语义重排序
    """

    def __init__(self):
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._vectorstore: Optional[Chroma] = None
        self._client: Optional[chromadb.PersistentClient] = None

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """延迟初始化嵌入模型"""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model="text-embedding-ada-002"
            )
        return self._embeddings

    @property
    def vectorstore(self) -> Chroma:
        """延迟初始化向量数据库"""
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                client=self._get_client(),
                collection_name="legal_documents",
                embedding_function=self.embeddings
            )
        return self._vectorstore

    def _get_client(self) -> chromadb.PersistentClient:
        """获取 Chroma 客户端"""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path="./data/chroma",
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        return self._client

    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        添加文档到向量库

        Args:
            documents: LangChain Document 对象列表
            ids: 可选的文档 ID 列表

        Returns:
            添加的文档 ID 列表
        """
        return self.vectorstore.add_documents(
            documents=documents,
            ids=ids
        )

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict] = None
    ) -> List[Document]:
        """
        向量相似度检索

        Args:
            query: 检索查询
            k: 返回的文档数量
            filter: 元数据过滤条件

        Returns:
            相关的 Document 对象列表
        """
        return self.vectorstore.similarity_search(
            query=query,
            k=k,
            filter=filter
        )

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        向量相似度检索（带分数）

        Args:
            query: 检索查询
            k: 返回的文档数量
            filter: 元数据过滤条件

        Returns:
            (Document, 相似度分数) 元组列表
        """
        return self.vectorstore.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter
        )

    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        vector_weight: float = 0.6,
        filter: Optional[dict] = None
    ) -> List[Tuple[Document, float]]:
        """
        混合检索：向量检索 + 关键词检索

        结合语义理解和精确关键词匹配，提高法律检索准确率

        Args:
            query: 检索查询
            k: 返回的文档数量
            vector_weight: 向量检索权重 (0-1)，关键词权重 = 1 - vector_weight
            filter: 元数据过滤条件

        Returns:
            (Document, 混合分数) 元组列表，按分数降序排列
        """
        dense_results = self.similarity_search_with_score(query, k=k * 2, filter=filter)

        keyword_scores = self._bm25_keyword_search(query, dense_results)

        hybrid_scores: List[Tuple[Document, float]] = []
        for doc, vector_score in dense_results:
            keyword_freq = keyword_scores.get(doc.metadata.get("chunk_id", ""), 0)
            combined_score = (vector_weight * (1 - vector_score) +
                           (1 - vector_weight) * keyword_freq)
            hybrid_scores.append((doc, combined_score))

        hybrid_scores.sort(key=lambda x: x[1], reverse=True)
        return hybrid_scores[:k]

    def _bm25_keyword_search(
        self,
        query: str,
        documents: List[Tuple[Document, float]]
    ) -> dict:
        """
        简化的 BM25 关键词评分

        Args:
            query: 查询文本
            documents: 候选文档

        Returns:
            {chunk_id: score} 字典
        """
        query_terms = set(query.lower().split())
        scores = {}

        for doc, _ in documents:
            chunk_id = doc.metadata.get("chunk_id", "")
            doc_terms = set(doc.page_content.lower().split())
            overlap = len(query_terms & doc_terms)
            scores[chunk_id] = overlap / len(query_terms) if query_terms else 0

        return scores

    def reset_collection(self):
        """重置向量库（谨慎使用）"""
        self.vectorstore.delete_collection()
        self._vectorstore = None


_retriever_service: Optional[LegalRetrieverService] = None


def get_retriever_service() -> LegalRetrieverService:
    """获取检索服务单例"""
    global _retriever_service
    if _retriever_service is None:
        _retriever_service = LegalRetrieverService()
    return _retriever_service
