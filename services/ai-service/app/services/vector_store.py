"""向量数据库服务 - Chroma"""
import os
import logging
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from chromadb.api.models.Collection import Collection
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    chromadb = None
    ChromaSettings = None
    Collection = None

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ChineseEmbeddingFunction:
    """中文嵌入函数 - 使用text2vec-base-chinese模型"""

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("shibing624/text2vec-base-chinese")

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, input: str) -> list[float]:
        embedding = self.model.encode(input, normalize_embeddings=True)
        return embedding.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def name(self) -> str:
        return "text2vec-base-chinese"


_embedding_function = None


def get_embedding_function():
    """获取嵌入函数（单例）"""
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = ChineseEmbeddingFunction()
    return _embedding_function


class VectorStore:
    """Chroma向量数据库封装"""

    def __init__(self, collection_name: str = "legal_docs"):
        if not HAS_CHROMADB:
            logger.warning("chromadb not installed, vector store unavailable")
            self.client = None
            self.collection = None
            self.collection_name = collection_name
            return

        self.persist_directory = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "chroma"
        )
        os.makedirs(self.persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = collection_name
        self.collection = None

    def get_or_create_collection(self):
        """获取或创建集合"""
        embedding_fn = get_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=embedding_fn,
            metadata={"description": "法律文档向量库"}
        )
        return self.collection

    def add_documents(self, documents: list[dict]):
        """添加文档到向量库

        Args:
            documents: 文档列表，每项包含 id, text, metadata
        """
        if not self.collection:
            self.get_or_create_collection()

        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None
    ) -> list[dict]:
        """向量检索

        Args:
            query: 查询文本
            top_k: 返回数量
            where: 元数据过滤条件
            where_document: 文档内容过滤条件

        Returns:
            检索结果列表
        """
        if not self.collection:
            self.get_or_create_collection()

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
            where_document=where_document
        )

        documents = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                documents.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None
                })

        return documents

    def delete_collection(self):
        """删除集合"""
        if self.collection:
            self.client.delete_collection(self.collection_name)
            self.collection = None

    def count(self) -> int:
        """获取集合中的文档数量"""
        if not self.collection:
            self.get_or_create_collection()
        return self.collection.count()


vector_store = VectorStore()


def search_legal_docs(query: str, top_k: int = 5) -> list[dict]:
    """检索法律文档的便捷函数"""
    return vector_store.search(query=query, top_k=top_k)