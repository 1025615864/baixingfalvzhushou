"""档案库向量库 - 支持本地Embedding和远程Embedding服务"""
import os
import logging
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1536

USE_REMOTE_EMBEDDING = os.getenv("USE_REMOTE_EMBEDDING", "false").lower() in {"true", "1", "yes"}
REMOTE_EMBEDDING_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8006")


class ChineseEmbeddingFunction:
    """本地中文嵌入函数"""

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


class RemoteEmbeddingFunction:
    """远程Embedding服务客户端"""

    def __init__(self, base_url: str = REMOTE_EMBEDDING_URL):
        self.base_url = base_url
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def embed_documents(self, texts: list[str], normalize: bool = True) -> list[list[float]]:
        """批量获取文档embedding"""
        try:
            client = await self._get_client()
            response = await client.post(
                "/embed/texts",
                json={"texts": texts, "normalize": normalize}
            )
            response.raise_for_status()
            data = response.json()
            return data["embeddings"]
        except Exception as e:
            logger.error(f"Remote embedding failed: {e}")
            return [[0.0] * EMBEDDING_DIM for _ in texts]

    async def embed_query(self, query: str, normalize: bool = True) -> list[float]:
        """获取查询embedding"""
        try:
            client = await self._get_client()
            response = await client.post(
                "/embed/query",
                json={"query": query, "normalize": normalize}
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]
        except Exception as e:
            logger.error(f"Remote embedding failed: {e}")
            return [0.0] * EMBEDDING_DIM


_embedding_function = None
_remote_embedding = None
_pgvector_store = None


def get_embedding_function():
    """获取本地嵌入函数（单例）"""
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = ChineseEmbeddingFunction()
    return _embedding_function


def get_remote_embedding() -> RemoteEmbeddingFunction:
    """获取远程嵌入函数"""
    global _remote_embedding
    if _remote_embedding is None:
        _remote_embedding = RemoteEmbeddingFunction()
    return _remote_embedding


def is_remote_embedding_enabled() -> bool:
    """是否启用远程embedding"""
    return USE_REMOTE_EMBEDDING


def get_vector_store_type() -> str:
    """获取向量存储类型: pgvector 或 chromadb"""
    return os.getenv("VECTOR_STORE_TYPE", "chroma").lower()


def get_pgvector_store():
    """获取pgvector存储实例"""
    global _pgvector_store
    if _pgvector_store is not None:
        return _pgvector_store

    try:
        from shared.vector.pgvector_store import get_vector_store

        database_url = os.getenv("ARCHIVE_DATABASE_URL")
        if not database_url:
            logger.warning("ARCHIVE_DATABASE_URL not set, using ChromaDB")
            return None

        _pgvector_store = get_vector_store(
            store_type="pgvector",
            database_url=database_url.replace("postgresql://", "postgresql+asyncpg://"),
            table_name="archive_vectors",
            embedding_dim=EMBEDDING_DIM
        )
        logger.info("pgvector store initialized for archive service")
        return _pgvector_store
    except Exception as e:
        logger.warning(f"Failed to initialize pgvector store: {e}")
        return None


class ArchiveVectorStore:
    """档案库向量数据库封装 - 支持本地/远程Embedding、ChromaDB/pgvector"""

    def __init__(self):
        self.persist_directory = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "chroma_archive"
        )
        os.makedirs(self.persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = "archive_cases"
        self.collection = None

    def get_or_create_collection(self):
        """获取或创建集合"""
        embedding_fn = get_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=embedding_fn,
            metadata={"description": "案例档案库向量库"}
        )
        return self.collection

    async def add_documents_async(self, documents: list[dict]):
        """异步添加文档到向量库"""
        store_type = get_vector_store_type()

        if store_type == "pgvector":
            await self._add_documents_pgvector_async(documents)
        else:
            await self._add_documents_chroma_async(documents)

    def add_documents(self, documents: list[dict]):
        """添加文档到向量库（同步，使用本地embedding）"""
        store_type = get_vector_store_type()

        if store_type == "pgvector":
            self._add_documents_pgvector_sync(documents)
        else:
            self._add_documents_chroma_sync(documents)

    async def _add_documents_pgvector_async(self, documents: list[dict]):
        """使用pgvector异步添加文档"""
        store = get_pgvector_store()
        if not store:
            logger.warning("pgvector not available, falling back to ChromaDB")
            await self._add_documents_chroma_async(documents)
            return

        try:
            embed_func = get_remote_embedding() if is_remote_embedding_enabled() else get_embedding_function()
            texts = [doc["text"] for doc in documents]

            if is_remote_embedding_enabled():
                embeddings = await embed_func.embed_documents(texts)
            else:
                embeddings = embed_func.embed_documents(texts)

            vectors = []
            for i, doc in enumerate(documents):
                vectors.append({
                    "id": doc["id"],
                    "embedding": embeddings[i],
                    "content": doc["text"],
                    "metadata": doc.get("metadata", {})
                })

            await store.add_vectors(vectors)
            logger.info(f"Added {len(vectors)} documents to pgvector")
        except Exception as e:
            logger.error(f"Failed to add to pgvector: {e}")
            await self._add_documents_chroma_async(documents)

    def _add_documents_pgvector_sync(self, documents: list[dict]):
        """使用pgvector同步添加文档"""
        store = get_pgvector_store()
        if not store:
            logger.warning("pgvector not available, falling back to ChromaDB")
            self._add_documents_chroma_sync(documents)
            return

        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                embedding_func = get_embedding_function()
                texts = [doc["text"] for doc in documents]
                embeddings = embedding_func.embed_documents(texts)

                vectors = []
                for i, doc in enumerate(documents):
                    vectors.append({
                        "id": doc["id"],
                        "embedding": embeddings[i],
                        "content": doc["text"],
                        "metadata": doc.get("metadata", {})
                    })

                loop.run_until_complete(store.add_vectors(vectors))
                logger.info(f"Added {len(vectors)} documents to pgvector")
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Failed to add to pgvector: {e}")
            self._add_documents_chroma_sync(documents)

    async def _add_documents_chroma_async(self, documents: list[dict]):
        """使用ChromaDB异步添加文档"""
        try:
            collection = self.get_or_create_collection()
            texts = [doc["text"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]

            if is_remote_embedding_enabled():
                embed_func = get_remote_embedding()
                embeddings = await embed_func.embed_documents(texts)
                collection.add(
                    ids=[doc["id"] for doc in documents],
                    embeddings=embeddings,
                    metadatas=metadatas
                )
            else:
                collection.add(
                    ids=[doc["id"] for doc in documents],
                    documents=texts,
                    metadatas=metadatas
                )
            logger.info(f"Added {len(documents)} documents to ChromaDB")
        except Exception as e:
            logger.error(f"Failed to add to ChromaDB: {e}")

    def _add_documents_chroma_sync(self, documents: list[dict]):
        """使用ChromaDB同步添加文档"""
        try:
            collection = self.get_or_create_collection()
            collection.add(
                ids=[doc["id"] for doc in documents],
                documents=[doc["text"] for doc in documents],
                metadatas=[doc["metadata"] for doc in documents]
            )
            logger.info(f"Added {len(documents)} documents to ChromaDB")
        except Exception as e:
            logger.error(f"Failed to add to ChromaDB: {e}")

    async def search_async(self, query: str, top_k: int = 5) -> list[dict]:
        """异步向量检索"""
        store_type = get_vector_store_type()

        if store_type == "pgvector":
            return await self._search_pgvector_async(query, top_k)
        else:
            return await self._search_chroma_async(query, top_k)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """向量检索（同步，使用本地embedding）"""
        store_type = get_vector_store_type()

        if store_type == "pgvector":
            return self._search_pgvector_sync(query, top_k)
        else:
            return self._search_chroma_sync(query, top_k)

    async def _search_pgvector_async(self, query: str, top_k: int) -> list[dict]:
        """使用pgvector异步搜索"""
        store = get_pgvector_store()
        if not store:
            logger.warning("pgvector not available, falling back to ChromaDB")
            return await self._search_chroma_async(query, top_k)

        try:
            embed_func = get_remote_embedding() if is_remote_embedding_enabled() else get_embedding_function()

            if is_remote_embedding_enabled():
                query_vector = await embed_func.embed_query(query)
            else:
                query_vector = embed_func.embed_query(query)

            results = await store.search(query_vector, top_k=top_k)

            documents = []
            for result in results:
                documents.append({
                    "id": result.id,
                    "text": result.content,
                    "metadata": result.metadata,
                    "distance": result.distance
                })
            return documents
        except Exception as e:
            logger.error(f"pgvector search failed: {e}")
            return await self._search_chroma_async(query, top_k)

    def _search_pgvector_sync(self, query: str, top_k: int) -> list[dict]:
        """使用pgvector同步搜索"""
        store = get_pgvector_store()
        if not store:
            logger.warning("pgvector not available, falling back to ChromaDB")
            return self._search_chroma_sync(query, top_k)

        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                embedding_func = get_embedding_function()
                query_vector = embedding_func.embed_query(query)

                results = loop.run_until_complete(store.search(query_vector, top_k=top_k))

                documents = []
                for result in results:
                    documents.append({
                        "id": result.id,
                        "text": result.content,
                        "metadata": result.metadata,
                        "distance": result.distance
                    })
                return documents
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"pgvector search failed: {e}")
            return self._search_chroma_sync(query, top_k)

    async def _search_chroma_async(self, query: str, top_k: int) -> list[dict]:
        """使用ChromaDB异步搜索"""
        try:
            collection = self.get_or_create_collection()

            if is_remote_embedding_enabled():
                embed_func = get_remote_embedding()
                query_vector = await embed_func.embed_query(query)
                results = collection.query(
                    query_embeddings=[query_vector],
                    n_results=top_k
                )
            else:
                results = collection.query(
                    query_texts=[query],
                    n_results=top_k
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
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            return []

    def _search_chroma_sync(self, query: str, top_k: int) -> list[dict]:
        """使用ChromaDB同步搜索"""
        try:
            collection = self.get_or_create_collection()
            results = collection.query(
                query_texts=[query],
                n_results=top_k
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
        except Exception as e:
            logger.error(f"ChromaDB search failed: {e}")
            return []

    def delete_collection(self):
        """删除集合"""
        if self.collection:
            self.client.delete_collection(self.collection_name)
            self.collection = None

    async def count_async(self) -> int:
        """异步获取集合中的文档数量"""
        store_type = get_vector_store_type()

        if store_type == "pgvector":
            store = get_pgvector_store()
            if store:
                try:
                    return await store.count()
                except Exception:
                    pass

        collection = self.get_or_create_collection()
        return collection.count()

    def count(self) -> int:
        """获取集合中的文档数量"""
        store_type = get_vector_store_type()

        if store_type == "pgvector":
            store = get_pgvector_store()
            if store:
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(store.count())
                    finally:
                        loop.close()
                except Exception:
                    pass

        collection = self.get_or_create_collection()
        return collection.count()


archive_vector_store = ArchiveVectorStore()


async def search_archive_async(query: str, top_k: int = 5) -> list[dict]:
    """异步检索档案库"""
    return await archive_vector_store.search_async(query=query, top_k=top_k)


def search_archive(query: str, top_k: int = 5) -> list[dict]:
    """检索档案库"""
    return archive_vector_store.search(query=query, top_k=top_k)


async def get_collection_count_async() -> int:
    """异步获取档案库文档数量"""
    return await archive_vector_store.count_async()


def get_collection_count() -> int:
    """获取档案库文档数量"""
    return archive_vector_store.count()
